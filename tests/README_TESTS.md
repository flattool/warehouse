# Writing unit tests for GNOME TypeScript and JavaScript applications

This is a small guide to writing unit tests for GNOME applications written in TypeScript and JavaScript.

# Why unit tests?

Unit tests are a key technique to ensure a bug-free application. They can:
- test various methods and functions in different scenarios to ensure the expected behaviour happens after refactoring bits of code. 
- take the burden off the developer to test every single niche case for every single build. 
- allow the testing of individual methods that would otherwise be impossible to call standalone
- run in a CI pipeline like GitHub Actions to ensure that your app works the way you expect
- lower the risk of regressions (bugs introduced after adding a feature/fixing another bug in an unrelated area)
# What are unit tests?
If you haven't written a unit test before, a unit test is a series of one or more *assertions*. Each unit test is considered `passed` if all assertions are true, otherwise it's considered `failed`.

Conceptually, each unit test boils down to a method that checks the result of different calls to the method being tested.
### Example

```ts
void add(term1: number, term2: number): number{
    return term1 + term2;
}

void testAdd(){
    assert(add(1, 2) === 3);
    assert(add(2, 5)==7);
}
```

This way, if we accidentally introduce bugs in the add method, the test would catch it early on, allowing us to fix them before users get to see the new version

## Writing tests for GTK apps
By default, GTK applications are **NOT** built in a unit-test friendly way. In order to use automated unit testing, the app should be written in such a way to allow testing. For a more deep dive into testable patterns in GTK apps watch Federico's talk about testing GTK apps linked in the [Resources](#resources-and-further-reading) section. The key point is, however, to isolate the business logic of your app in a *separate* class from your widget.

Let's assume we have a small calculator app. The app has 1 screen with 2 `Gtk.Entry` widgets for each of the 2 terms, 5 `Gtk.Button` widgets for the operations we can do on the numbers and a `Gtk.Label` to show the result



**Bad example**

```ts
//button_box.ts
//<imports are skipped>
@GObjectify.Class({template: "/io/github/flattool/Warehouse/button_box" })
export class CalculatorWidget extends Adw.Bin{

    @GObjectify.Child
    private accessor firstTermEntry!: Gtk.Entry;
    @GObjectify.Child
    private accessor secondTermEntry!: Gtk.Entry;
    @GObjectify.Child
    private accessor resultLabel!: Gtk.Label;
    @GObjectify.Child
    private accessor addButton!: Gtk.Button;
    @GObjectify.Child
    private accessor subButton!: Gtk.Button;
    @GObjectify.Child
    private accessor mulButton!: Gtk.Button;
    @GObjectify.Child
    private accessor divButton!: Gtk.Button;
    @GObjectify.Child
    private accessor powButton!: Gtk.Button;

    constructor(){
        super();
        /// This callback cannot be tested because we need a button to be clicked before it can get executed
        addButon.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            /// How can we test the result?
            resultLabel.set_text((term1 + term2).toString());
        });
        subButton.connect("clicked", () => { 
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            /// How can we test the result?
            resultLabel.set_text((term1 - term2).toString());
        });
        mulButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            /// How can we test the result?
            resultLabel.set_text((term1 * term2).toString());
        });
        divButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            /// Is this sufficient to guard against divisions by 0?
            /// What would happen that happened?
            resultLabel.set_text((term1 / term2).toString());
        });
        powButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            /// How can we test the result?
            resultLabel.set_text((term1 ** term2).toString());
        });
    }
}

```
As you can see all the business logic of the application is packed inside these handlers, which cannot be easily called automatically by a CI pipeline. What's more in order to test JUST those callback we'd need to instantiate the entire GTK apparatus
**Good example**

```ts
//button_box.ts
//<imports are skipped>

class Calculator{
    public add(term1: number, term2: number): number{
        return term1 + term2;
    }
    public sub(term1: number, term2: number): number{
        return term1 - term2;
    }
    public mul(term1: number, term2: number): number{
        return term1 * term2;
    }
    public div(term1: number, term2: number): number{
        return term1 / term2;
    }
    public pow(term1: number, term2: number): number{
        return term1 ** term2;
    }
}
@GObjectify.Class({template: "/io/github/flattool/Warehouse/button_box" })
export class CalculatorWidget extends Adw.Bin{

    @GObjectify.Child
    private accessor firstTermEntry!: Gtk.Entry;
    @GObjectify.Child
    private accessor secondTermEntry!: Gtk.Entry;
    @GObjectify.Child
    private accessor resultLabel!: Gtk.Label;
    @GObjectify.Child
    private accessor addButton!: Gtk.Button;
    @GObjectify.Child
    private accessor subButton!: Gtk.Button;
    @GObjectify.Child
    private accessor mulButton!: Gtk.Button;
    @GObjectify.Child
    private accessor divButton!: Gtk.Button;
    @GObjectify.Child
    private accessor powButton!: Gtk.Button;

    constructor(){
        super();
        /// This callback cannot be tested because we need a button to be clicked before it can get executed
        addButon.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            let calculator: Calculator = Calculator();
            /// The logic is separated from the widget, can be tested separately
            resultLabel.set_text(calculator.add(term1, term2).toString());
        });
        subButton.connect("clicked", () => { 
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            let calculator: Calculator = Calculator();
            /// The logic is separated from the widget, can be tested separately
            resultLabel.set_text(calculator.sub(term1, term2).toString());
        }); 
        mulButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let calculator: Calculator = Calculator();
            /// The logic is separated from the widget, can be tested separately
            resultLabel.set_text(calculator.mul(term1, term2).toString());
        });
        divButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            let calculator: Calculator = Calculator();
            // We can now separately test for divisions by 0
            resultLabel.set_text(calculator.div(term1, term2).toString());
        });
        powButton.connect("clicked", () => {
            let term1: number =+this.firstTermEntry.get_text();
            let term2: number =+this.secondTermEntry.get_text();
            let calculator: Calculator = Calculator();
            resultLabel.set_text(calculator.pow(term1, term2).toString());
        });
    }
}
```

The important thing to keep in mind is that **unit tests can ONLY check the RETURN value(s) of a method. They CANNOT test method-local variables**. This is why when creating methods you should have each method do **one thing and one thing only**

# Adding a new test
## File structure
```
tests/
├── meson.build # here test files are declared
├── README_TESTS.md
└── sources # here the test source files are written
    ├── my_object_tests.ts
    ├── my_other_object_tests.ts
    ...
```
## Test file
How to add a test:
- Step 1: make a new `.ts` file in `tests/sources/` (e.g. `testDemo.ts`)
- Step 2: add the file name, without the `.ts` extension in the `tests` dictionary inside `tests/meson.build`

```diff
unit_tests = {
    'doubly_linked_list_test': {},
++  'testDemo': {}  
}
```
- Step 3: Import the objects you're going to test. **Make sure you use RELATIVE paths TO THE TEST FILE**. Make sure you import them as `.js` and that you *write the extension as well*
```diff
// testDemo.ts
++ import { Calculator } from "../../src/calculator.js";

```
- Step 4: Import Jasmine and declare the methods you're going to use
```diff
// testDemo.ts
import { Calculator } from "../../src/calculator.js";

++ declare function describe(...args: any[]): any
++ declare function it(...args: any[]): any
++ declare function expect(...args: any[]): any
++ declare function beforeEach(...args: any[]): any
```

- Step 5: Add your test(s)
```diff
import { Calculator } from "../../src/calculator.js";

declare function describe(...args: any[]): any
declare function it(...args: any[]): any
declare function expect(...args: any[]): any
declare function beforeEach(...args: any[]): any


++ describe("Test Operations", () => {
++    it("testAdd", () => {
++        let calculator: Calculator = Calculator();
++        expect(calculator.add(1, 2)).toBe(3);
++    });
++    it("testSub", () => {
++        let calculator: Calculator = Calculator();
++        expect(calculator.sub(1, 2)).toBe(-1);
++    });
//and so on
++});
```

# Running tests
## While building locally
Simply run the `run.sh` script. Tests will be run automatically before your app runs.
## In a CI pipeline
Use the Flatpak GitHub Action to trigger tests. See [the resources](#resources-and-further-reading) for more details.
# Test-Driven-Development
A common technique is to first make the unit tests for a particular object THEN write the actual object, in a very hacky way at first, then refactor while keeping an eye on the success rate of the test so that you don't introduce regressions

### Steps
1. Write test
2. Make a hacky implementation that passes the tests
3. Refactor
4. Run tests again
5. If any anciliary tests fail, fix the bugs, then go to step 3 until the code structure looks good
# Common errors
| Problem                                    | Solution                                                                                                                                                                       |
|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tests don't run                            | Check your `tests/meson.build` file and make sure the affected test is added to the dictionary. Make sure that the run-tests variable in the flatpak manifest is set to `true` and make sure meson setup has the `-Dtests=true` option given to it.|
| `expect`, `it`, ... could be found         | Make sure you have declared the function definitions. You have to do that for every file.                                                                                       |
| Module `src/foo/bar.ts` could not be found | You have used a path relative to the top-level project directory. The path MUST be relative to the TEST FILE. `src/foo/bar.ts` => `../../src/foo/bar.ts`                       |
| Can't find `fooTest.ts` | You have declared `fooTest` in the `meson.build` file but haven't created the file in the right location                       |
# Resources and further reading

- [Have a GTK app with no tests? No problem (Federico Mena Quintero, GUADEC 2025, Track 1, Day 2)](https://www.youtube.com/live/18Ir6RXkIeA?t=20285&si=txFPmHUWuj5WA0Dy)
- [Jasmine testing framework API reference](https://jasmine.github.io/pages/docs_home.html)
- [Test-driven development](https://www.geeksforgeeks.org/software-engineering/test-driven-development-tdd/)
- [Flatpak GitHub Actions](https://github.com/flatpak/flatpak-github-actions)
