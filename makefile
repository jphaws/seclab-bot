.PHONY: good fail

make:
good:
	@echo "Server is running, run the client yourself to test"
	@while (true) ; do cat tests/allgood | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug ; done
fail:
	@echo "Server is running, run the client yourself to test"
	@echo "This testcase will give you one good response (so the client can init) and then give bad responses"
	@cat tests/allgood | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug
	@while (true) ; do cat tests/fail | openssl s_server -accept 8080 -nocert -cipher "ALL" -debug ; done

