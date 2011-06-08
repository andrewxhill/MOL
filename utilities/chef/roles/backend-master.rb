name "backend-master"
description "this is a sample chef role for an app server"
default_attributes "config" => { 
      "firewall" => { 
        "rules" => ["ACCEPT net fw tcp 80","ACCEPT net fw tcp 8080",ACCEPT net fw tcp 22"] 
    } 
}
run_list(
    "recipe[ror]",
    "recipe[shorewall]"
   
)
