name "backend-master"
description "this is a sample chef role for an app server"
default_attributes "config" => { 
      "firewall" => { 
        "rules" => ["ACCEPT net 80", "ACCEPT net fw tcp 8080", "ACCEPT net 4000" ,"ACCEPT    net    22"] 
    } 
}
run_list(
    "recipe[build-essential]",
    "recipe[runit]",
    "recipe[nginx]",
    "recipe[python]",
    "recipe[pylons]",
    "recipe[git]",
    "recipe[postgres]",
    "recipe[postgres_client]",
    "recipe[gdal]",
    "recipe[geos]",
    "recipe[proj]",
    "recipe[postgis]",
    "recipe[redis]",       
    "recipe[nodejs]",
    "recipe[windshaft]" ,
    "recipe[mol-layers]"      
)
