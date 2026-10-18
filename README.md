# 🛡️ HOMOSEC — Homoglyph Security Toolkit

**Your Toolkit Against Visual Impersonation Attacks**

HOMOSEC is a Python-based cybersecurity toolkit designed to identify suspicious Unicode characters, visually deceptive text, and potential homoglyph-based impersonation attempts. It provides a unified graphical interface for analyzing strings, checking suspicious domains, inspecting email addresses and URLs, auditing password strength, and scanning filenames for potentially deceptive characters.

The project focuses on a subtle but important security problem: malicious actors can exploit characters that look nearly identical to legitimate letters or numbers to impersonate trusted websites, users, and organizations.

Built with Python and Tkinter, HOMOSEC combines Unicode normalization, character-mapping techniques, visual similarity analysis, and security-oriented scanning utilities in a neon-inspired interface.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [What Are Homoglyph Attacks?](#-what-are-homoglyph-attacks)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [Usage Guide](#-usage-guide)
- [Example Scenarios](#-example-scenarios)
- [Project Structure](#-project-structure)
- [Limitations](#-limitations)
- [Future Improvements](#-future-improvements)
- [Security and Privacy](#-security-and-privacy)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

Homoglyph attacks exploit characters from different writing systems or character sets that appear visually similar. For example, a Cyrillic character may resemble a Latin character closely enough to deceive someone inspecting a website address or email sender.

HOMOSEC helps users investigate such cases by transforming text into a normalized representation, identifying suspicious character substitutions, and comparing visually deceptive strings.

The application brings multiple analysis utilities together in one desktop interface, making it useful for cybersecurity learning, Unicode security research, phishing-awareness exercises, and controlled security testing.

### 🎯 Project Objectives

- Detect potentially deceptive characters in text and identifiers.
- Identify strings that become equivalent after configured character folding.
- Highlight suspicious characters and explain their mappings.
- Investigate domains that may be attempting to imitate legitimate websites.
- Examine email addresses and links for suspicious domain characters.
- Evaluate basic password-strength indicators and homoglyph usage.
- Identify suspicious filenames within a selected directory.
- Provide an accessible graphical interface for security analysis.

---

## 🧠 What Are Homoglyph Attacks?

A homoglyph is a character that looks similar or identical to another character but may have a different Unicode code point.

Attackers can exploit these similarities to create deceptive usernames, domain names, URLs, email addresses, or filenames.

For example:

| Legitimate-looking text | Deceptive-looking text | Potential issue |
|---|---|---|
| `paypal.com` | `pаypal.com` | The second string contains a Cyrillic character resembling Latin `a`. |
| `google.com` | `goog1e.com` | The number `1` can be mistaken for the letter `l`. |
| `microsoft.com` | `micrоsoft.com` | The second string can contain a Cyrillic `о` instead of Latin `o`. |
| `john_doe` | `j0hn_doe` | A number replaces a visually similar letter. |

**Why does this matter?**

- **Phishing:** A deceptive domain can imitate a trusted brand.
- **Email impersonation:** A sender address may look legitimate at first glance.
- **Identity spoofing:** Similar-looking usernames can be used to impersonate another account.
- **Filename deception:** A filename can contain unusual characters that conceal its apparent identity.
- **Security awareness:** Users may overlook differences that are obvious at the Unicode level but difficult to notice visually.

HOMOSEC helps expose these differences through character analysis and normalization.

---

## ✨ Features

### 1. 🔤 String Comparison

Compare two strings to determine whether they produce the same normalized representation under the configured homoglyph rules.

Features include:

- Side-by-side string comparison.
- Unicode normalization and character folding.
- Optional lowercase conversion.
- Optional diacritic stripping.
- Highlighting of characters that differ from their folded representations.
- Detailed breakdown of recognized character substitutions.
- Identification of character categories such as Greek, Cyrillic, Latin Extended, and Leetspeak.

**Example:**

Compare `paypal.com` with `pаypal.com`, where the second string contains a visually similar Cyrillic character.

The tool can identify the character substitution and determine whether both strings fold to the same representation.

### 2. 🔎 String Scanner

Scan a single string for suspicious characters and character sequences.

The scanner can report:

- The detected character or sequence.
- Its normalized replacement.
- Its position in the input.
- Its recognized homoglyph category.
- A highlighted preview of the original string.

This feature is useful for inspecting usernames, domain names, filenames, and other text-based identifiers.

### 3. 🌐 Phishing Domain Checker

Analyze a domain or URL for characters that may be used to imitate a legitimate domain.

The checker provides:

- Domain normalization and homoglyph detection.
- A folded representation for comparison.
- A heuristic similarity score.
- Optional DNS A-record lookup when `dnspython` is installed.
- A demonstration threat-feed check using predefined examples.

**Important:** The built-in threat-feed entries and takedown workflow are simulated demonstrations. They do not represent a live threat-intelligence service or an actual domain takedown operation. The similarity score is a heuristic, not a probability that a domain is malicious.

### 4. 📧 Email and Link Scanner

Inspect an email address or pasted text containing email addresses and URLs.

The scanner extracts recognizable email addresses and HTTP/HTTPS links, examines their domains for suspicious homoglyphs, and displays potential findings.

Useful for:

- Examining suspicious sender addresses.
- Reviewing links copied from an email.
- Investigating visually deceptive domains.
- Practicing phishing identification in a controlled environment.

This is a text-analysis utility rather than a full email-client integration or comprehensive email-header analyzer.

### 5. 🔐 Password Auditor

Evaluate a password using basic strength heuristics and homoglyph analysis.

The auditor considers:

- Password length.
- Character variety, including lowercase, uppercase, digits, and symbols.
- A small built-in list of common password words.
- Simple repeated-character patterns.
- Selected keyboard and sequential patterns.
- Potentially confusing characters.

The tool assigns a qualitative rating, such as Weak, Moderate, Strong, or Excellent, based on its scoring rules.

**Note:** This is an educational password auditor, not a complete password-security assessment. Its rating does not guarantee resistance to guessing, cracking, or credential attacks.

### 6. 📁 Filename Scanner

Select a directory to scan filenames for suspicious homoglyphs.

The scanner:

- Traverses the selected directory and its subdirectories.
- Examines filenames against the configured homoglyph map.
- Displays the filename and whether suspicious characters were detected.
- Reports the total number of flagged files.

The current implementation examines filenames rather than analyzing file contents or determining whether files are malicious.

### 7. 🔬 Homoglyph Visualizer

Explore characters that map to the same normalized representation.

Enter a character or word to view matching homoglyphs recognized by the configured mapping.

This helps users understand how different Unicode characters can resemble one another and how normalization influences detection.

### 8. ⏱️ Repeated URL Analysis

The URL monitoring tab repeatedly scans a user-supplied URL at five-second intervals.

It displays timestamped results indicating whether configured homoglyph rules identify suspicious characters in the supplied URL.

The monitor runs its scanning loop in a background thread to keep the interface responsive.

**Scope:** This is repeated analysis of the entered URL string. It does not passively monitor browser traffic, inspect network packets, or automatically discover URLs visited by the user.

### 9. 🌍 Unicode Normalization

HOMOSEC uses Python's built-in `unicodedata` functionality to normalize Unicode text.

The folding process can include:

- NFKC Unicode normalization.
- Optional lowercase conversion.
- Optional removal of diacritical marks.
- Mapping configured homoglyphs to a common representation.
- Longest-key-first matching for mapped character sequences.

The resulting representation helps reveal strings that appear different in their original form but become equivalent under the selected rules.

### 10. 📚 External Confusables Mapping

The application supports importing a compatible Unicode `confusables.txt` file to expand its mapping rules.

This allows users to investigate a wider range of Unicode confusables beyond the built-in mappings.

The effectiveness of this feature depends on the supplied file, its format, and the application's mapping implementation.

### 11. 🎨 Neon Cybersecurity Interface

The graphical interface uses Python's Tkinter and themed widgets to provide a cyberpunk-inspired appearance.

Interface highlights include:

- Dark background.
- Neon green and cyan accents.
- Tab-based navigation.
- Highlighted findings.
- Structured result tables.
- Input validation and user notifications.
- A home screen introducing the toolkit.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3 | Core application and detection logic |
| Tkinter | Desktop graphical interface |
| `unicodedata` | Unicode normalization and character categories |
| `re` | Pattern matching and extraction of email addresses and URLs |
| `difflib` | Heuristic string-similarity calculations |
| `urllib.parse` | URL parsing |
| `os` | Directory traversal and filename scanning |
| `threading` | Background execution for repeated URL analysis |
| `time` | Monitoring timestamps and intervals |
| `dnspython` | Optional DNS A-record lookup |
| `collections` | Grouping and organizing homoglyph findings |

Most of the application's core functionality uses Python's standard library. The `dnspython` package is optional and enables the DNS lookup feature.

---

## ⚙️ How It Works

HOMOSEC uses a mapping-based detection process to identify suspicious characters.

### Step 1: Accept Input

The user supplies a string, domain, email address, URL, password, or directory to analyze.

### Step 2: Normalize Unicode

The application applies Unicode NFKC normalization to standardize supported character representations.

Depending on the selected options, it can also convert text to lowercase and remove diacritical marks.

### Step 3: Apply Homoglyph Mappings

The application checks the normalized text against its configured mapping rules, which include selected characters and sequences associated with:

- Latin Extended characters.
- Greek characters.
- Cyrillic characters.
- Full-width characters.
- Leetspeak substitutions.
- Other explicitly configured lookalikes.

If an external confusables mapping is loaded, the application can use those additional rules as well.

### Step 4: Generate a Folded Representation

Suspicious characters or sequences are converted into their configured replacement representation.

For example, a string containing a supported Cyrillic lookalike may fold to the same representation as a Latin-only string.

### Step 5: Compare or Report Findings

The application uses the folded representation or scanner findings to display results.

Depending on the selected feature, the results can include:

- A match or difference verdict.
- Original and normalized strings.
- Detected characters and their categories.
- Character positions and replacements.
- Heuristic scores or supplementary DNS results.
- A highlighted preview.

### Step 6: Interpret the Results

A finding indicates that a configured rule matched the input. It does not automatically establish that a website, email, file, or account is malicious.

Unicode normalization and homoglyph mappings are useful detection techniques, but the results depend on the mappings and heuristics used.

---

## 📦 Installation

### Prerequisites

- Python 3 installed on your system.
- Tkinter support available in your Python installation.
- An internet connection if you want to perform DNS lookups.
- The optional `dnspython` package for DNS functionality.

Check your Python installation:

```bash
python --version
```

On systems where Python is invoked through `python3`, use:

```bash
python3 --version
```

### 1. Clone the Repository

Replace the placeholder below with your actual GitHub repository URL.

```bash
git clone https://github.com/YOUR_USERNAME/HOMOSEC.git
cd HOMOSEC
```

Alternatively, download the repository as a ZIP file and extract it.

### 2. Install the Optional DNS Dependency

```bash
python -m pip install dnspython
```

This dependency enables DNS A-record lookups in the phishing-domain checker. The application is designed to handle its absence by disabling that capability.

### 3. Verify Tkinter

On Windows, Tkinter is commonly included with standard Python installations.

To check whether it is available, run:

```bash
python -m tkinter
```

If a test window opens, Tkinter is available.

On Linux, you may need to install your distribution's Tkinter package. For example, on Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3-tk
```

---

## ▶️ Running the Application

Navigate to the directory containing your Python script.

If your main file is named `new.py`, run:

```bash
python new.py
```

If you have renamed it to `homosec.py`, run:

```bash
python homosec.py
```

The HOMOSEC desktop application should open with its home screen and analysis tabs.

Use the interface to select the feature you want to explore.

---

## 🧪 Usage Guide

### Compare Two Strings

1. Open the **Compare Strings** tab.
2. Enter the first string.
3. Enter the second string.
4. Run the comparison.
5. Review the verdict, folded representations, and character breakdown.

Example inputs:

```text
String A: paypal
String B: pаypal
```

The second input should contain the Cyrillic `а` character, not the ordinary Latin `a`.

### Scan a String

1. Open the **Scan String** tab.
2. Enter a string.
3. Run the scan.
4. Review the detected characters, replacements, positions, and highlighted preview.

Example:

```text
@amaz0n_support
```

The scanner can flag configured substitutions such as `@` and `0`.

### Check a Domain

1. Open the **Phishing Domains** tab.
2. Enter a domain or URL.
3. Run the check.
4. Review the folded representation, any heuristic score, and available DNS results.

Use a known test string or a domain you are authorized to investigate.

### Scan Email Text

1. Open the **Emails** tab.
2. Paste an email address, URL, or relevant text containing links.
3. Start the scan.
4. Review any suspicious sender addresses or links reported by the application.

### Audit a Password

1. Open the **Password Auditor** tab.
2. Enter a test password.
3. Run the audit.
4. Review the homoglyph findings and qualitative strength rating.

Use synthetic test passwords rather than real account credentials when experimenting with the tool.

### Scan Filenames

1. Open the **File Scanner** tab.
2. Select a directory.
3. Wait for the recursive filename scan to complete.
4. Review the results and the number of suspicious filenames.

### Visualize Homoglyphs

1. Open the **Homoglyph Visualizer** tab.
2. Enter a character or word.
3. Run the visualization.
4. Review the recognized alternatives and their categories.

### Monitor a URL

1. Open the **Real-time URL Monitor** tab.
2. Enter a URL string.
3. Start monitoring.
4. Review the repeated scan results.
5. Stop monitoring when finished.

---

## 🧩 Example Scenarios

The following examples illustrate inputs that can be useful for controlled testing.

| Test input | What to investigate |
|---|---|
| `j0hn_doe` | Digit-to-letter substitutions |
| `goog1e` | Number and letter lookalikes |
| `pаypal.com` | Cyrillic and Latin character confusion |
| `micrоsoft.com` | Cross-script domain impersonation |
| `@amaz0n_support` | Leetspeak-style substitutions |
| `facеbook` | A potentially deceptive character in a brand-like string |

Some examples contain non-ASCII Unicode characters that may look identical to their Latin equivalents. Their exact behavior depends on the active mappings and normalization settings.

---

## 📂 Project Structure

A suggested repository layout is:

```text
HOMOSEC/
│
├── new.py                  # Main application (rename if desired)
├── README.md               # Project documentation
├── Homoglyph_Examples.docx # Example inputs and test cases
├── requirements.txt        # Optional dependency list
├── LICENSE                 # Project license, if selected
│
└── screenshots/            # Optional application screenshots
```

This is a suggested layout, not a claim that every file or folder already exists in your repository. Adjust the filenames to match your actual project.

A minimal `requirements.txt` for the optional DNS feature can contain:

```text
dnspython
```

The core application otherwise relies primarily on the Python standard library.

---

## ⚠️ Limitations

HOMOSEC is a security-analysis and educational toolkit. It should not be treated as a complete phishing-detection platform or a substitute for a comprehensive security solution.

Important limitations include:

- **Rule-based detection:** Results depend on the configured homoglyph mappings. Unknown or unmapped characters may not be detected.
- **False positives:** Legitimate multilingual text can contain characters that resemble Latin letters.
- **False negatives:** Some deceptive strings may bypass the current rules or input-extraction patterns.
- **Similarity scores:** The displayed score is heuristic and must not be interpreted as a calibrated probability of maliciousness.
- **Threat-feed simulation:** The predefined threat examples and takedown messages are simulated and do not connect to a live threat-intelligence provider.
- **DNS checks:** DNS resolution can confirm that a record is returned, but it cannot establish that a domain is safe or malicious.
- **Password auditing:** The strength rating is based on simple rules and does not replace modern password-strength estimation or password-cracking analysis.
- **Filename scanning:** The current file scanner analyzes filenames, not the underlying file contents.
- **URL monitoring:** Repeated scans inspect the entered URL string; they do not monitor live browser or network traffic.
- **Email analysis:** The scanner examines recognizable email addresses and links in supplied text. It is not a full mail gateway or email-header forensic system.

A clean result means only that the current checks did not identify a matching suspicious pattern. It is not a guarantee of safety.

---

## 🚀 Future Improvements

Potential enhancements for future versions include:

- Integrating an authoritative Unicode confusables dataset with improved mapping validation.
- Improving internationalized domain name and Punycode analysis.
- Adding configurable allowlists and blocklists.
- Integrating reputable threat-intelligence APIs.
- Improving domain comparison with trusted-domain baselines.
- Supporting structured reports and exportable scan results.
- Adding automated unit tests for Unicode edge cases.
- Improving detection accuracy and measuring false-positive and false-negative rates.
- Enhancing password analysis with more robust strength-estimation techniques.
- Adding file-content inspection as a separate, explicitly scoped feature.
- Supporting configurable monitoring intervals and improved monitoring controls.
- Improving accessibility and interface customization.
- Adding packaging for easier desktop installation.

These are possible extensions, not features claimed to be fully implemented in the current version.

---

## 🔒 Security and Privacy

HOMOSEC is intended to support defensive security analysis and authorized testing.

- Use the toolkit only on systems, files, domains, and data you are authorized to examine.
- Avoid entering real account passwords or sensitive credentials during demonstrations.
- Treat detection results as indicators for further investigation, not definitive verdicts.
- Verify suspicious domains through independent, trusted security resources.
- Do not rely on a single heuristic to make high-impact security decisions.
- Remember that the phishing threat-feed and takedown workflow in the current implementation are demonstrations, not operational services.

---

## 🤝 Contributing

Contributions that improve detection accuracy, usability, testing, and documentation are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request describing the change and its purpose.

Suggested contribution areas include Unicode edge cases, additional test cases, improved error handling, mapping validation, accessibility, and documentation.

---

## 📄 License

No license is specified here. Before publishing the repository, select a license that reflects how you want others to use, modify, and distribute your project, and add the corresponding `LICENSE` file.

---

## 👨‍💻 Project Summary

**HOMOSEC — Homoglyph Security Toolkit** brings Unicode-based impersonation analysis and several supporting security checks into a single Python desktop application.

By combining Unicode normalization, configurable homoglyph mappings, string comparison, domain inspection, email and URL analysis, password auditing, filename scanning, and a cyberpunk-inspired interface, the project demonstrates practical techniques for investigating visually deceptive text.

**Built with Python. Focused on Unicode security. Designed to help expose visual impersonation.**
