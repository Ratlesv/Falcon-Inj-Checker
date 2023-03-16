# Falcon-Inj-Checker
Sql URL injection Checker
---------------------------------

--urls: The path to the file containing the list of URLs you want to check for SQL injection vulnerabilities. The default is "urls.txt".

--proxies: A comma-separated list of proxies to use for sending requests. 
The default is "http://127.0.0.1:24000,http://127.0.0.1:24001,http://127.0.0.1:24002".

--timeout: The timeout for each request in seconds. The default is 10 seconds.

--output: The path to the output file where SQL injectable URLs will be saved. The default is "result.txt".



To run the script with these arguments, you can use a command like this:

python Falcon-Inj-Checker.py --urls my_urls.txt --proxies http://proxy1:port,http://proxy2:port --timeout 15 --output injectable_urls.txt

This command will check the URLs in the "my_urls.txt" file using the specified proxies with a 15-second timeout for each request. The script will save any potentially SQL-injectable URLs in the "injectable_urls.txt" file.
