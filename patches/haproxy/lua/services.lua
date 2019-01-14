-- Module for OpenStack services.
--
-- This module contains the list of services (i.e., Service Type,
-- Interface, Region and URL) of each OpenStack instances. Services
-- are indexed first by the name of the Region.
--
-- Provides:
-- - services.lookup_by_reg_url(reg, url):
--   Lookup in the list of services the actual "Service Type" and
--   "Interface" of a specific region `reg` and URL `url`.

local json     = require('json')
local inspect  = require('inspect')
local services = {}

-- See http://lua-users.org/wiki/StringRecipes
local function starts_with(str, start)
   return str:sub(1, #start) == start
end

-- Open and decode a json file
--
-- @param filename the json file
-- @return a lua array
local function json_file(filename)
    local file = io.open(filename, "r" )
    if file then
        local contents = file:read( "*a" )
        local json_table = json.decode(contents);
        io.close( file )
        return json_table
    else
        core.log(core.err, "File not found")
    end
    return nil
end

-- Indexes services per "Region" name.
--
-- @param filename json file with a list of json objects containing
-- the "Region", "Service Type", "Interface" and "URL" fields.
-- @return a list of services indexed region name.
local function services_per_regions(filename)
  local json_regions = json_file(filename)
  local regions = {}

  for _, entry in ipairs(json_regions['services']) do
    if regions[entry["Region"]] == nil then
      regions[entry["Region"]] = {}
    end
    table.insert(regions[entry["Region"]], entry)
  end

  core.log(core.info,'regions: '..inspect(regions))
  return regions
end

-- List of all OpenStack services (i.e, "Service Type", "URL",
-- "Interface" and "Region") indexed by the "RegionName".
--
-- Regions ADT:
-- regions := { RegionName: Service ... , ... }
-- Service := { "URL": str,
--              "Service Type": str,
--              "Region": RegionName,
--              "Interface": str
--            }
local regions = services_per_regions("/etc/haproxy/services.conf")

-- Lookup for a service based on a specific region `reg`
-- and predicate p on a service
--
-- @param reg the region name
-- @param p Service -> Bool
-- @return a Service object.
function services.lookup(reg, p)
  local region = regions[reg]

  if region then
    for _, service in pairs(region) do
      if p(service) then
        core.log(core.info,'lookup_service: '..inspect(service))
        return service
      end
    end

    core.log(core.err, 'Cannot find service for region '..
               inspect(reg)..' and url '..inspect(url))
  else
    core.log(core.err, 'Cannot find service for region '..
               inspect(reg)..' and url '..inspect(url))
  end

  return nil
end

-- Lookup for a service based on a specific region `reg`
-- and URL `url`.
--
-- @return a Service object.
function services.lookup_by_reg_url(reg, url)
  local region = regions[reg]

  if region then
    for _, service in pairs(region) do
      if starts_with(url, service["URL"]) then
        core.log(core.info,'lookup_service: '..inspect(service))
        return service
      end
    end

    core.log(core.err, 'Cannot find service for region '..
               inspect(reg)..' and url '..inspect(url))
  else
    core.log(core.err, 'Cannot find service for region '..
               inspect(reg)..' and url '..inspect(url))
  end

  return nil
end

return services
