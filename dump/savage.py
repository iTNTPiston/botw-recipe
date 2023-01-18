import dukpy
from adapter import BaseAdapter, bootstrap

_ES5_CODE = """

Array.prototype.includes = function (item, start) {
    if (!start) {
        start = 0;
    }
    for (var i=start; i<this.length; i++) {
        if (this[i] === item) {
            return true;
        }
    }
    return false;
}

// from https://github.com/jsPolyfill/Array.prototype.find/blob/master/find.js
Array.prototype.find = Array.prototype.find || function(callback) {
  if (this === null) {
    throw new TypeError('Array.prototype.find called on null or undefined');
  } else if (typeof callback !== 'function') {
    throw new TypeError('callback must be a function');
  }
  var list = Object(this);
  // Makes sures is always has an positive integer as length.
  var length = list.length >>> 0;
  var thisArg = arguments[1];
  for (var i = 0; i < length; i++) {
    var element = list[i];
    if ( callback.call(thisArg, element, i, list) ) {
      return element;
    }
  }
};

"""

#
ORIGINAL_UNIQUE = "function unique(z) { return __spreadArray([], __read(new Set(z)), false); }"
GLUE_UNIQUE = """

function unique(z) {
    var a = [];
    new Set(z).forEach(function(x){a.push(x)});
    return a;
}

"""

def load_file(interpreter, name):
    with open(name, "r", encoding="utf-8") as js_file:
        interpreter.evaljs("\n".join(js_file.readlines()))

class SavageRecipeAdapter(BaseAdapter):
    def __enter__(self):
        super().__enter__()
        interpreter = dukpy.JSInterpreter()
        # glue in some initialization code
        interpreter.evaljs("var exports = {};")
        # glue in code to support JS features not included with dukpy
        interpreter.evaljs(_ES5_CODE)
        load_file(interpreter, "adapters/setjs/set.js")
        load_file(interpreter, "adapters/stringpadStart/index.js")
        # load bundle
        with open("bundle.js", "r", encoding="utf-8") as js_file:
            bundle_js = "\n".join(js_file.readlines())
            bundle_js = bundle_js.replace(ORIGINAL_UNIQUE,GLUE_UNIQUE)

        interpreter.evaljs(bundle_js)
        # glue in more initialization code
        interpreter.evaljs("var pot = new exports.CookingData();")
        self.js = interpreter
        return self

    def get_data(self, items):
        return self.js.evaljs(f"pot.cook_hp(dukpy.items)", items=items)

if __name__ == "__main__":
    bootstrap(SavageRecipeAdapter)