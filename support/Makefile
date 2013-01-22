CFLAGS = -Wall -pedantic -ansi
CC = gcc

SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:.c=.o)
TARGET = soluzione
INPUTS = $(wildcard input-*.txt)
DIFFS = $(INPUTS:input-%.txt=diffs-%.txt)

compile = $(CC) $(CFLAGS) -c -o $@ $<
link = $(CC) $^ -o $@
test = ./soluzione $$\(cat args-$*.txt\) \< $< \> $@

exit_on_fail = true

red := bash -c 'echo -ne "\033[31m"'
blue := bash -c 'echo -ne "\033[34m"'
reset := bash -c 'echo -ne "\033[0m"'

.PHONY: compila test pulisci

compila: $(TARGET) ;

test: $(DIFFS) ;

pulisci:
	@rm -f *.o .compile-* .link-* .errors-* actual-*.txt diffs-*.txt $(TARGET) \~*

%.o: %.c
	@rm -f .compile-$*
	@echo $(compile)
	@if ! $(compile) -fmessage-length=0 2> .compile-$*; then\
		echo "error: compiler exited with error: $$?" > .compile-$*;\
	fi
	@if grep -q warning: .compile-$*; then\
		$(red);\
		grep ': warning:' .compile-$*;\
		$(reset);\
	fi
	@if grep -q error: .compile-$*; then\
		$(blue);\
		grep ': error:' .compile-$*;\
		$(reset);\
		exit 1;\
	fi

$(TARGET): $(OBJECTS)
	@rm -f .link-$@
	@echo $(link)
	@$(link) -fmessage-length=0 2> .link-$@ || true
	@if [ -s .link-$@ ]; then\
		$(blue);\
		cat .link-$@;\
		$(reset);\
		exit 1;\
	fi

.PRECIOUS: actual-%.txt

actual-%.txt: input-%.txt args-%.txt $(TARGET)
	@rm -f .errors-$* $@
	@echo $(test)
	@if ! bash -c "ulimit -t 2; ./$(TARGET) $$(cat args-$*.txt) < $< > $@" 2> .errors-$*; then\
		if grep -Eqi 'bash: line 1:.*(Killed|Cputime limit exceeded)' .errors-$*; then\
			$(blue);\
			echo execution timeout 1>&2;\
			$(reset);\
		elif grep -Eqi 'bash: line 1:.*Segmentation fault' .errors-$*; then\
			$(red);\
			echo segmentation fault 1>&2;\
			$(reset);\
		else\
			$(red);\
			echo non-zero return value 1>&2;\
			$(reset);\
		fi;\
		rm $@;\
		if $(exit_on_fail); then exit 1; fi;\
	fi


diffs-%.txt: output-%.txt actual-%.txt
	@echo diff -b $^ \> $@
	@diff -b $^ > $@ 2> /dev/null || true
	@if [ -s $@ ]; then\
	 	$(red);\
	 	cat $@;\
		$(reset);\
		if $(exit_on_fail); then exit 1; fi;\
	fi;\
	echo "test:$*: ok"
