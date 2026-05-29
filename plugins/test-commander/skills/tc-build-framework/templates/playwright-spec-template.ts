// Spec template - rendered by /tc:automate into tests/e2e/<area>.spec.ts.
// One spec per @area: feature; one test() per automate-ranked scenario.
// The provenance comment below is mandatory and machine-readable: it links the
// generated test back to its requirement and candidate scenario so
// /tc:traceability-map can resolve the Automated test column.
import { test, expect } from '@playwright/test';
import { <AreaName>Page } from '../pages/<AreaName>Page';

test.describe('<requirement title>', () => {
  // @req:<REQ-ID> @cs:<CS-ID>
  test('<scenario title>', async ({ page, <fixtureName> }) => {
    const <areaName> = new <AreaName>Page(page);
    await <areaName>.goto();

    // Steps map from the scenario's Given/When/Then. Data comes from the
    // fixture (<fixtureName>), never inlined here (Decision D6).
    await <areaName>.<behaviorName>();

    await expect(page).toHaveURL(/<expected-path>/);
  });
});
