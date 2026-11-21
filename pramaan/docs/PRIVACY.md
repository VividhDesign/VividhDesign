# Privacy policy

*Plain-language starting point; have it reviewed before launching a paid service. Written with India's
Digital Personal Data Protection Act, 2023 in mind.*

## The browser version (vividhdesign.github.io/pramaan)

* **Your document never leaves your device.** The checker runs inside your browser tab.
* **What the page downloads:**
  * the program and a public index of judgments, from the site;
  * the Python runtime (Pyodide), from the jsDelivr CDN;
  * public judgment PDFs, from the open dataset's server (Amazon S3), when it checks a quoted passage.
    These requests reveal which judgment is being fetched, not your document.
* No cookies, analytics or accounts.

## The hosted API and server

* **Documents are processed in memory and discarded** when the response is sent. They are not written
  to disk, logged, or used for training.
* **What is recorded, for billing and abuse prevention:**
  * the API key;
  * the time of the request;
  * the number of citations checked;
  * the number flagged high-risk.

  For requests without a key, the IP address is held in memory for the day's limit and not saved.
* Usage records are kept for 12 months for billing, then deleted.
* No data is sold or shared, except where the law requires it.

## Contact

Questions or deletion requests: [your contact email].
