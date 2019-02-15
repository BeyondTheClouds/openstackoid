--   ____                ______           __        _    __
--  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
-- / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
-- \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
--     /_/
-- Make your OpenStacks Collaborative
--
-- Module for OpenStack services.
--
-- This module contains the list of services (i.e., Service Type,
-- Interface, Region and URL) of each OpenStack instances. And,
-- provides function to lookup services.
--
-- Provides:
-- * services.lookup(p):
--   Returns the first service that satisfies the predicate p.
--
-- * services.lookup_by_reg(p):
--   Returns the first service of region `reg` that satisfies
--   the predicate p.
--
-- * services.lookup_by_url(url):
--   Returns the first service whose the service["URL"]
--   matches `url`.
--
-- * services.lookup_by_reg_url(reg, url):
--   Returns the first service of region `reg` whose the
--   service["URL"] matches `url`.

local json     = require('json')
local inspect  = require('inspect')
local services = {}

-- See http://lua-users.org/wiki/StringRecipes
local function starts_with(str, start)
   return str:sub(1, #start) == start
end

-- Open and decode a json file.
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
local function services_per_regions(services)
  local regions = {}

  for _, entry in ipairs(services) do
    if regions[entry["Region"]] == nil then
      regions[entry["Region"]] = {}
    end
    table.insert(regions[entry["Region"]], entry)
  end

  core.log(core.info,'regions: '..inspect(regions))
  return regions
end

-- List of all OpenStack services (i.e, "Service Type", "URL",
-- "Interface" and "Region").
--
-- service ADT
-- services := [ Service ... ]
-- Service := { "URL": str,
--              "Service Type": str,
--              "Region": RegionName,
--              "Interface": str
--            }
local _services = json_file("/etc/haproxy/services.json")["services"]

-- List of all OpenStack services (i.e, "Service Type", "URL",
-- "Interface" and "Region") indexed by the "Region".
--
-- Regions ADT:
-- regions := { RegionName: Service ... , ... }
local regions = services_per_regions(_services)

-- Lookup for a service based on a predicate `p`.
--
-- @param p a predicate Service -> Bool
-- @return a Service object.
function services.lookup(p)
  for _, service in pairs(_services) do
    if p(service) then
      core.log(core.info,'lookup_service: '..inspect(service))
      return service
    end
  end

  core.log(core.err, 'Cannot find service by predicate '..inspect(p))

  return nil
end

-- Lookup for a service based on a specific URL `url`.
--
-- @return a Service object.
function services.lookup_by_url(url)
  local function starts_with_url(service)
    return starts_with(url, service["URL"])
  end

  return services.lookup(starts_with_url)
end

-- Lookup for a service based on a specific region `reg`
-- and predicate `p` on a service.
--
-- @param reg the region name
-- @param p a predicate Service -> Bool
-- @return a Service object.
function services.lookup_by_reg(reg, p)
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
  local function starts_with_url(service)
    return starts_with(url, service["URL"])
  end

  return services.lookup_by_reg(reg, starts_with_url)
end

return services
