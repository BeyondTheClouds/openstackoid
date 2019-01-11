-- Module for scope interpretation.
--
--
-- This Lua script redirects requests based on
-- HTTP request port or path.
-- See,
-- http://www.arpalert.org/src/haproxy-lua-api/1.8/index.html
-- http://haproxy.tech-notes.net/7-3-6-fetching-http-samples-layer-7/

local inspect  = require('lua.inspect')
local json     = require('lua.json')
local services = require('lua.services')

local current_region = "RegionOne"

-- Returns the scope of the request.
local function get_scope(headers)
  -- Initialize to default scope
  local scope = {
    ["compute"]   = current_region,
    ["identity"]  = current_region,
    ["image"]     = current_region,
    ["network"]   = current_region,
    ["placement"] = current_region
  }

  -- Update the default scope with values in `s`.
  --
  -- This function prevents to fully fill the scope at the OpenStack
  -- CLI.
  local function update_scope(s)
    for k, v in pairs(s) do
      scope[k] = v
    end
  end

  -- Let's find the scope in the headers
  local x_scope = headers["x-scope"]
  local x_auth_scope = headers["x-auth-token"]

  if x_scope then
    -- X-Scope header, the scope is here
    core.log(core.info, 'x-scope: '..inspect(x_scope))
    update_scope(json.decode(x_scope[0]))
  elseif x_auth_scope then
    -- Oh X-Auth-Token, OK then scope maybe be there
    core.log(core.info,'x-auth-token: '..inspect(x_auth_scope))

    local i,j = string.find(x_auth_scope[0], "!SCOPE!")
    if i then -- Yeah! scope is here
      update_scope(
        json.decode(
          string.sub(x_auth_scope[0], j+1, #x_auth_scope[0])))
    end
  end

  core.log(core.info, 'scope: '..inspect(scope))
  return scope
end

-- Remove !SCOPE! from X-*-Token.
--
-- @param token_name, the name of the X-*-Token, e.g., X-Auth-Token,
-- or X-Subject-Token.
local function clean_token_header(token_name, txn)
  local x_star_header = txn.http:req_get_headers()[string.lower(token_name)] 

  if x_star_header then
    -- OK, the header exists
    local i, _ = string.find(x_star_header[0], "!SCOPE!")
    if i then -- Scope is here, let's clean the stuff
	    local token_value = string.sub(x_star_header[0], 0, i-1)
	    txn.http:req_set_header(token_name, token_value)
    end
  end
end

-- Extract the scope of the request and interpret it.
local function interpret_scope(txn)
  local url = txn.sf:base()
  local headers = txn.http:req_get_headers()

  -- Get the current service
  local current_service = services.lookup_by_reg_url(current_region, url)

  -- Find the scope and targeted region
  local scope = get_scope(headers)
  local targeted_region = scope[current_service["Service Type"]]
  core.log(core.info, 'targeted region: '..inspect(targeted_region))

  -- Compute the backend name
  local targeted_service_type = current_service["Service Type"]
  local targeted_interface = current_service["Interface"]
  local backend_name =
    targeted_region .."_".. targeted_service_type .."_".. targeted_interface
  core.log(core.info, 'backend name: '..inspect(backend_name))

  -- Clean X-*-Token headers
  clean_token_header("X-Subject-Token", txn)
  if targeted_service_type == "identity" then
    clean_token_header("X-Auth-Token", txn)
  end

  -- Add X-Identity-* for identity_server of keystone middleware
  local function is_admin_identity(service) 
    return service["Service Type"] == "identity"
      and service["Interface"] == "admin"
  end
  local id_service = services.lookup(scope["identity"], is_admin_identity)
  txn.http:req_set_header("X-Identity-Region", id_service["Region"])
  txn.http:req_set_header("X-Identity-Url",    id_service["URL"])

  return backend_name
end

core.register_fetches("interpret_scope", function(txn)
  -- Only works with http txn, no tcp
  if txn.sf:req_fhdr("host")..txn.sf:path() == "" then
    return
  else
    return interpret_scope(txn)
  end
end)