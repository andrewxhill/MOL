#
# Cookbook Name:: postgis
# Recipe:: default
#
# Copyright 2010, ProtectedPlanet.net
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Install postGIS 1.4
include_recipe 'gdal'
include_recipe 'geos'
include_recipe 'proj'
include_recipe 'postgres'
package 'postgis'
package 'postgresql-8.4-postgis'


# UPDATE TO PG 1.5 and fast GEOS, GDAL AND PROJ
bash "upgrade to postgis 1.5" do
  user "root"  
  code <<-EOH    
  add-apt-repository ppa:ubuntugis/ubuntugis-unstable
  apt-get update
  apt-get install -y libgeos-3.2.2
  apt-get remove -y libgeos-3.1.0 libgeos-dev
  apt-get upgrade -y postgis
  apt-get install -y libgeos-dev  
  EOH
end

# BASIC GIS TEMPLATE SETUP
bash "configure postgis" do
  user "root"  
  code <<-EOH    
  createdb  -T template0 -O postgres -U postgres -E UTF8 template_postgis
  createlang plpgsql -U postgres -d template_postgis
  psql -d template_postgis -U postgres -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql
  psql -d template_postgis -U postgres -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql
  ldconfig
  EOH
  only_if { `psql -U postgres -t -c "select count(*) from pg_catalog.pg_database where datname = 'template_postgis'"`.include? '0'}
end

# create non-postgres user in Cap
# allow postgres users to connect from other AWS - in the pg_hba.conf