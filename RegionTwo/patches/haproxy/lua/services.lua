-- Module for OpenStack services.
--
-- This module contains the list of services (i.e., Service Type,
-- Interface, Region and URL) of each OpenStack instances. Services
-- are indexed first by the name of the Region and then by "Service
-- Type++Interface".
--
-- Provides:
-- - services.lookup_service_interface(reg, url):
--   Lookup in the list of services the actual "Service Type" and
--   "Interface" of a specific region `reg` and URL `url`.

local json     = require('lua.json')
local inspect  = require('lua.inspect')
local services = {}

-- See http://lua-users.org/wiki/StringRecipes
local function starts_with(str, start)
   return str:sub(1, #start) == start
end

-- Open and decode a json file
--
-- filename: the json file
-- returns a lua array
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

-- Indexes services per "Service Type++Interface" and "Region".
--
-- filename: json file with a list of json objects containing the
-- "Region", "Service Type", "Interface" and "URL" fields.
local function services_per_regions(filename)
  local json_regions = json_file(filename)
  local regions = {}

  for _, entry in ipairs(json_regions) do
    if regions[entry["Region"]] == nil then
      regions[entry["Region"]] = {}
    end
    table.insert(regions[entry["Region"]], entry)
  end

  core.log(core.info,'regions: '..inspect(regions))
  return regions
end

-- List of all OpenStack services (i.e, "Service Type", "URL",
-- "Interface" and "Region") indexed first by the "Region" and then by
-- the "Service Type++Interface".
--
-- Regions ADT:
-- regions := { RegionName: Service ... , ... }
-- Service := { "URL": str,
--              "Service Type": str,
--              "Region": RegionName,
--              "Interface": str
--            }
local regions = services_per_regions("services.conf")

-- Lookup in `service.regions` the actual "Service Type" and
-- "Interface" of a specific region `reg` and URL `url`.
--
-- returns a Service object.
function services.lookup_service(reg, url)
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
