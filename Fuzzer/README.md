# Web Directory Fuzzer

A beginner cybersecurity practice project focused on web directory enumeration and multithreaded scanning using Python.

## Description

This project was created to practice:

* HTTP request handling with Python
* Web directory enumeration
* Multithreading with ThreadPoolExecutor
* Response status code analysis
* Browser header emulation
* Working with wordlists
* Basic reconnaissance techniques used in cybersecurity labs

The script scans a target website using a directory wordlist and checks for accessible directories and hidden paths.

## Features

* Multithreaded directory scanning
* Custom User-Agent browser emulation
* HTTP status code detection
* Timeout and connection error handling
* Displays accessible directories after scan completion
* Lightweight and beginner-friendly

## Technologies Used

* Python 3
* requests
* concurrent.futures
* urllib.parse

## Example Use Cases

* Cybersecurity lab practice
* Learning web enumeration techniques
* Beginner penetration testing exercises
* Networking and HTTP response analysis

## Important Notice

This project is intended for educational purposes and authorized testing only. Do not scan websites without permission.

## How to Run

```bash
pip install requests
python directory_fuzzer.py
```

## Example Wordlist

```bash
admin
login
dashboard
uploads
backup
```

