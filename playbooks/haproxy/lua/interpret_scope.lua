--   ____                ______           __        _    __
--  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
-- / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
-- \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
--     /_/
-- Make your OpenStacks Collaborative
--
-- Module for scope interpretation.
--
-- This Lua script redirects requests based on the HTTP request and a
-- scope.
--
-- HAProxy Lua Doc:
-- * http://www.arpalert.org/src/haproxy-lua-api/1.8/index.html
-- * http://haproxy.tech-notes.net/7-3-6-fetching-http-samples-layer-7/
-- * https://www.haproxy.com/documentation/aloha/9-0/traffic-management/lb-layer7/http-rewrite/

local inspect  = require('inspect')
local json     = require('json')
local services = require('services')

-- Returns the scope of the request.
local function get_scope(headers, current_region)
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
local function interpret_scope(txn, current_region)
  local url = txn.sf:base()
  local headers = txn.http:req_get_headers()
  core.log(core.info, 'receive req: '..inspect(url))

  -- Get the service of the `url`
  local service = services.lookup_by_url(url)
  local targeted_service_type = service["Service Type"]
  local targeted_interface = service["Interface"]

  if not service then
    -- If the current request do not target a service, then use the
    -- transparent backend.
    core.log(core.info, 'Use transparent backend')
    return 'transparent'
  elseif service['Region'] ~= current_region then
    -- If the service is in a different cloud than the actual
    -- HAProxy (i.e., the request is already forged to target a
    -- service from another cloud) thus do not bother to lookup
    -- into scope -- this is the case in keystone-middleware for
    -- instance.
    local targeted_region = service["Region"]
    local backend_name =
      targeted_region .."_".. targeted_service_type .."_".. targeted_interface

    core.log(core.info, 'backend name: '..inspect(backend_name))
    return backend_name
  end

  -- Find the scope and targeted region
  local scope = get_scope(headers, current_region)
  local targeted_region = scope[service["Service Type"]]
  core.log(core.info, 'targeted region: '..inspect(targeted_region))

  -- Compute the backend name
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
  local id_service = services.lookup_by_reg(scope["identity"], is_admin_identity)
  txn.http:req_set_header("X-Identity-Cloud", id_service["Region"])
  -- FIXME: find the proper protocol (e.g., http, https) instead of hardcoding it
  txn.http:req_set_header("X-Identity-Url", "http://"..id_service["URL"])

  return backend_name
end

core.register_fetches("interpret_scope", function(txn, current_region)
  -- Only works with http txn, no tcp
  if txn.sf:req_fhdr("host")..txn.sf:path() == "" then
    return
  else
    return interpret_scope(txn, current_region)
  end
end)
