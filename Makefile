CFLAGS = -Wall -pedantic -ansi
CC = gcc

SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:.c=.o)
TARGET = soluzione
INPUTS = $(wildcard input-*.txt)
OUTPUTS = $(wildcard output-*.txt)
ARGS = $(wildcard args-*.txt)
DIFFS = $(INPUTS:input-%.txt=diffs-%.txt)

compile = $(CC) $(CFLAGS) -o $@ -c $<
link = $(CC) $(LDFLAGS) $^ -o $@
test = ./soluzione $$\(cat args-$*.txt\) \< $< \> $@

red := bash -c 'echo -ne "\033[31m"'
blue := bash -c 'echo -ne "\033[34m"'
reset := bash -c 'echo -ne "\033[0m"'

.PHONY: clean

target: $(TARGET) ;

test: $(DIFFS) ;

clean:
	@rm -f *.o .compile.* .link.* actual-*.txt diffs-*.txt $(TARGET)

%.o: %.c
	@rm -f .compile.$@
	@echo $(compile)
	@$(compile) -fmessage-length=0 2> .compile.$* || true
	@if grep -q warning: .compile.$*; then\
		$(red);\
		grep ': warning:' .compile.$*;\
		$(reset);\
		fi
	@if grep -q error: .compile.$*; then\
		$(blue);\
		grep ': error:' .compile.$*;\
		$(reset);\
		exit 1; fi

$(TARGET): $(OBJECTS)
	@rm -f .link
	@echo $(link)
	@$(link) -fmessage-length=0 2> .link.$@ || true
	@if grep -q "1 exit status" .link.$@; then\
		$(blue);\
		cat .link.$@;\
		$(reset);\
		exit 1; fi

.PRECIOUS: actual-%.txt

actual-%.txt: input-%.txt args-%.txt $(TARGET)
	@echo $(test)
	@if ! ./$(TARGET) $$(cat args-$*.txt) < $< > $@; then\
		$(blue);\
		echo non-zero return value;\
		rm $@;\
		$(reset);\
		exit 1; fi

diffs-%.txt: output-%.txt actual-%.txt
	@echo diff -ub $^ \> $@
	@diff -ub $^ > $@ || true
	@if [ -s $@ ]; then\
	 	$(blue);\
		cat $@;\
		$(reset);\
		fi
