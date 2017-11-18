# Release Notes
## 0.2
### 0.2.2
* Refactor documentation into sections and tutorials.
* Create this release notes document for better version understanding.

### 0.2.1
* Refactor to remote the demo `bin` scripts and rewire for direct call of the
  script `classify_image.py` as the primary interaction mechanism.

### 0.2.0
* Refactor for compliant dataframe usage following primary client library
  examples for repeated columns (e.g. dataframes) instead of custom types
  that parsed rows individually.
* Refactor web, api, main model wrapper code for corresponding changes.
* Migration from previous library structure to new acumos client library
* Refactor to not need **this** library as a runtime/installed dependency

