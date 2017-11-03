# Creates Wn.tree file for odd numbered Wolfram 1D rule 1 to 255.
# Author: Tony Smith (ts@meme.com.au), January 2010.
# Derived in part from Golly/Rules/TreeGenerators/RuleTreeGen.pl.

# Generated rules use Mark Jeronimus's approach of a next line of state 2 cells,
# so need to run oddWolfram_init.pl on any seed pattern before using this rule.

use strict;

my ( @bits, %world, $nodeseq, @r, @params );

my $numStates = 3;
my $numNeighbors = 8;
my $numParams = $numNeighbors + 1;

# my $result = g_getstring("Please enter an odd integer from 1 to 255:",
#                          "193", "Create odd-valued Wolfram rule");
my $result =<STDIN>;
my $odd = int($result);
if ( $odd < 1 || $odd > 255 || ($odd & 1) == 0 ) {
   print "Given number must be odd and from 1 to 255.";
}

# print 
my $rule = $odd;
foreach my $bit ( 0 .. 7 ) { $bits[$bit] = $rule & 1; $rule = $rule >> 1 }
%world = ();
$nodeseq = 0;
@r = ();
@params = (0) x $numParams;
recur($numParams);
# my $ruledir = g_getdir("rules");
# my $ruledir = g_getdir("rules");



my $ruledir = "/home"; ### storage directory 



print "Creating W$odd.tree in \n".$ruledir;
open ( NEW, '>', $ruledir."W$odd.tree" ) || die "Cannot open file for output!";
print NEW "num_states=$numStates\n";
print NEW "num_neighbors=$numNeighbors\n";
print NEW "num_nodes=", scalar @r, "\n";
print NEW "$_\n" for @r ;
close NEW;

# g_new("untitled");
# g_setrule("W$odd");
# g_show("Done.  Enter a seed pattern and run oddWolfram_init.pl.");

sub f {
   my ($nw, $ne, $sw, $se, $n, $w, $e, $s, $c) = @_ ;
   if ( $nw == 2 or $n == 2 or $ne == 2 ) { return 2 } # allow widening patterns
   elsif ( $c != 2 ) { return $c }                     # past rows
   else { return $bits[ 4 * $nw + 2 * $n + $ne ] }     # next row
}

sub recur {
   my $at = shift;
   return f(@params) if $at == 0;
   my $n = $at;
   for (my $i=0; $i<$numStates; $i++) {
      $params[$numParams-$at] = $i;
      $n .= " " . recur($at-1);
   }
   return $world{$n} if defined($world{$n});
   $world{$n} = $nodeseq;
   push @r, $n;
   return $nodeseq++;
}

