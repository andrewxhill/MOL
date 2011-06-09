maintainer        "Andrew W. Hill"
maintainer_email  "andrewxhill@gmail.com"
license           "Apache 2.0"
description       "Clone and setup MOL"
long_description  IO.read(File.join(File.dirname(__FILE__), 'README.rdoc'))
version           "0.10.2"

recipe "mol", "Clone and setup MOL from Github"

%w{ ubuntu debian }.each do |os|
  supports os
end

%w{ nginx python}.each do |cb|
  depends cb
end
