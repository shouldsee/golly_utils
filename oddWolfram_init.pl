# Validates 1D rule/seed combination and adds next line indicator cells.
# Author: Tony Smith (ts@meme.com.au), January 2010.

# This must be run with a seed pattern on a single line before running any odd W rule
# to set up as per Mark Jeronimus's approach of adding a next line of state 2 cells.

use strict;

g_exit( 'There is no pattern.' ) if g_empty();
my $rulestring = g_getrule();
my ( $rule, $bounds ) = split( ':', $rulestring );
g_exit( 'Only for odd W rules.' ) unless $rule =~ s/W// and $rule > 0 and $rule < 256 and $rule % 2 == 1;
my @seedrect = g_getrect();
g_exit( 'Seed pattern must be only one cell high.' ) unless $seedrect[3] == 1;
my $cells = g_getcells( @seedrect );
if ( scalar @$cells % 2 ) { # may contain some state 2 cells
  my @replace;
  while ( scalar @$cells ) {
    my @cell = splice( @$cells, 0, 3 );
    $cell[2] = 1 if $cell[2] == 2; # convert any state 2 to state 1 in case seeded by randfill
    push( @replace, @cell );
  }
  g_putcells( \@replace );
}
my $width = g_getwidth();
my ( $left, $right );
if ( $width ) { # bounded
  $left  = - int ( $width / 2 );
  $right = $width + $left;
}
else { # unbounded
  $left  = $seedrect[0] - 1;
  $right = $seedrect[0] + $seedrect[2];
}
for ( my $x = $left; $x < $right; $x ++ ) { g_setcell( $x, $seedrect[1] + 1, 2 ) }
