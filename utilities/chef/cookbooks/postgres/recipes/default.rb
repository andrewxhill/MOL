#
# Cookbook Name:: postgres
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
package "postgresql-8.4"
package "postgresql-server-dev-8.4"
package "pgtune"

gem_package "pg" do
  action :install
  version "0.9.0"
end  

service "postgresql" do
  service_name "postgresql"
  supports :restart => true, :status => true, :reload => true
end

# Allow any user to connect to postgres
# SETUP FOR ACCESS OVER EC2 IP's WITH PASSWORDS
template "/etc/postgresql/8.4/main/pg_hba.conf" do
  source "pg_hba.conf.erb"
  owner "postgres"
  group "postgres"
  mode 0600
  notifies :restart, resources(:service => "postgresql"), :immediately
end

# Expand memory that is available to postgres, good for postgres only boxes
memory = `cat /proc/meminfo | grep "MemTotal"`.match(/\d+/).to_s.to_i * 1024
shared_memory = (memory / 1.5).floor
current_shared_memory = File.read("/proc/sys/kernel/shmmax").to_i
execute "setup-shmmax" do
  command "echo #{shared_memory} > /proc/sys/kernel/shmmax"
  action :run
  only_if { shared_memory > current_shared_memory }
end

template "/etc/postgresql/8.4/main/postgresql.conf" do
  source "postgresql.conf.erb"
  mode 0644
  owner "postgres"
  group "postgres"  
	variables(
		:ram_mb => memory / 1024 / 1024
	)
	notifies :restart, resources(:service => "postgresql")  , :immediately
end

execute "run pg_tune" do
  command "pgtune -i /etc/postgresql/8.4/main/postgresql.conf -T Web -o /etc/postgresql/8.4/main/postgresql.conf.pgtune && cp -f /etc/postgresql/8.4/main/postgresql.conf.pgtune /etc/postgresql/8.4/main/postgresql.conf"
	notifies :restart, resources(:service => "postgresql")  , :immediately
  not_if { File.exists? "/etc/postgresql/8.4/main/postgresql.conf.pgtune"}
end

log "[POSTGRESQL] Update the postgres users password. ***CURRENTLY EMPTY***"
log "[POSTGRESQL] Run pgtune to get best out of box"
