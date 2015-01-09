import java.util.Scanner;
public class Soluzione {
	public static void main( String[] args ) {
		int x, y;
		Scanner sc = new Scanner(System.in);
		x = Integer.parseInt( args[ 0 ] );
		y = sc.nextInt();
		System.out.println( y - x );
	}
}
