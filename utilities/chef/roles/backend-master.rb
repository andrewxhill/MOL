name "backend-master"
description "this is a sample chef role for an app server"
default_attributes "config" => { 
      "firewall" => { 
        "rules" => ["ACCEPT net 80","ACCEPT net fw tcp 8080","ACCEPT    net    22"] 
    } 
}
run_list(
    "recipe[build-essential]",
    "recipe[runit]",
    "recipe[nginx]",
    "recipe[python]",
    "recipe[pylons]",
    "recipe[git]"
)

directory "#{molrepo}" do
  owner 'root'
  group 'root'
  mode 0755
end
