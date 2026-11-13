import { isMissing } from "./check.js";
test("missing values", () => {
  expect(isMissing(null)).toBe(true);
  expect(isMissing(undefined)).toBe(true);
  expect(isMissing(0)).toBe(false);
});
