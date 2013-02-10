#include <stdio.h>
#include <stdlib.h>

int main( int argc, char *argv[] )
{
	int x, y;

	x = atoi( argv[ 1 ] );
	scanf( "%d", &y );
	printf( "%d\n", y - x );

	return 0;
}
