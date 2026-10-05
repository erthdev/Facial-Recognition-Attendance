# Test Cases

Automated = `pytest 04_Testing -v`. Manual = run in the live app; record the result in the last column.

| ID | Test | Expected result | How | Result |
| --- | --- | --- | --- | --- |
| T01 | Enroll with a clear face and consent | Saved, 3+ encodings stored | pytest (db) + manual | |
| T02 | Enroll without consent | Rejected | pytest | |
| T03 | Duplicate student number | Rejected, nothing partially saved | pytest | |
| T04 | Photo with no face | "No face found" | pytest (detector stubbed) + manual (hand over lens) | |
| T05 | Photo with 2 faces | "Multiple faces" | pytest (detector stubbed) + manual | |
| T06 | Dark and blurry images | Quality error | pytest | |
| T07 | PDF renamed to .jpg | "Invalid image" | pytest | |
| T08 | Enrolled person scans | Recognized, Present | pytest (rules) + manual | |
| T09 | Same person scans again within 30 min | Duplicate message, no new row | pytest (rules) + manual | |
| T10 | Scan after the cutoff time | Status = Late | pytest (rules) + manual | |
| T11 | Unenrolled person scans | Unknown | pytest (rules) + manual | |
| T12 | Printed photo or phone screen | Record result; document the limitation | manual | |
| T13 | Database file renamed or locked | Friendly error, no crash | pytest | |
| T14 | Report for a date with no data | Empty-state message | pytest + manual | |
| T15 | CSV export | Opens with correct columns | pytest + manual | |
| T16 | Corrupt encoding in the DB | Sample skipped, warning logged | pytest | |
| T17 | Webcam unplugged or blocked in Chrome | Clear camera message | manual | |

## Accuracy measurement
Enrolled N = __ people, 10 scans each, threshold = __

| Correct matches | False rejections | False accepts | Avg. seconds per scan |
| --- | --- | --- | --- |
| | | | |
