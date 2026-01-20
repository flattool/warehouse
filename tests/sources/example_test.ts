declare function describe(...args: any[]): any
declare function it(...args: any[]): any
declare function expect(...args: any[]): any
declare function beforeEach(...args: any[]): any

describe("Sample test fixture", () => {
   
    it("Dummy test. Should pass if configuration is correct.", () => {
        
        expect(true).toBe(true);
    });
});