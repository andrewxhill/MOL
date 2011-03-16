function Foo(name, age) {
    this.setName(name);
    this.setAge(age);
    return this.getName() + ' is ' + this.getAge();
};

Foo.prototype = (
    function () {
        var name = 'aaron';
        var age = 23;        
        return {
            getName: function() {
                return name;
            },
            setName: function(val) {
                name = val;
                this.bar();
            },
            getAge: function() {
                return age;
            },
            setAge: function(val) {
                age = val;
            }            
        };        
}());


Foo.prototype.bar = function() {
    console.log('build row!');
};
