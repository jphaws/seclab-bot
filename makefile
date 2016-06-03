make:
testgood:
	@echo "Server is running, run the client yourself to test"
	while (true) ; do cat tests/allgood | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug ; done
testfail:
	@echo "Server is running, run the client yourself to test"
	cat tests/allgood | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug
	while (true) ; do cat tests/fail | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug ; done
