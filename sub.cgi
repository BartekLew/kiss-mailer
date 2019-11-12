#!/usr/bin/env perl

use strict;
use warnings;

my $subf = 'subs.dat';
my $reqf = 'req.dat';

sub error {
    my ($status, $msg) = @_;
    print("Status: $status\n\n$msg\n");
    exit;
}

sub keygen {
    open(my $rnd, "<:raw", "/dev/urandom")
        or die "can't open random number generator";

    my $n = read($rnd, my $data, 15);
    my $result = "";

    for my $c (split //, $data) {
        $result .= sprintf "%lx", ord $c;
    }

    close $rnd;

    return $result;
}

sub search_email {
    my ($fd, $email) = @_;

    seek $fd, 0, 0;
    while (my $l = <$fd>) {
        print "$l";
        my @dat = split /\|/, $l;

        for (my $i = 0; $i < scalar @dat; $i++) {
            $dat[$i] =~ s/^\s+|\s+$//g;
        }

        print "'$dat[0]' == '$email'\n";
        if($dat[0] eq $email) {

            return @dat;
        }
    }

    return undef;
}

my $email = lc(<STDIN>);
my $name = <STDIN>;

$email =~ s/^\s+|\s+$//g;
$name =~ s/^\s+|\s+$//g;

unless($email and $name and $name) {
    error(400, "Missing email or name (needed 2 lines)");
}

unless($email =~ /^[a-zA-Z_0-9.]+@[a-zA-Z_0-9.]+$/) {
    error(400, "$email: wrong email");
}

open(my $subfile, '+>>', $subf)
    and open(my $reqfile, '+>>', $reqf)
    or error(500, "Can't touch either: $subf $reqf.");

seek($subfile, 0, 0);
seek($reqfile, 0, 0);

if(search_email $subfile, $email) {
    error(400, "$email: already subscribing!");
}

if(search_email $reqfile, $email) {
    error(400, "$email: requested subscribtion!");
}

my $key = keygen();
print $reqfile "$email | $name | $key\n";

close($subfile);
close($reqfile);
