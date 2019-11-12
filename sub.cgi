#!/usr/bin/env perl

use strict;
use warnings;

my $subf = 'subs.dat';
my $reqf = 'req.dat';
my $template = 'message.html';
my $linkbase = "http://it.wiedz.net.pl/cgi-bin/sub.cgi";

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
        my @dat = split /\|/, $l;

        for (my $i = 0; $i < scalar @dat; $i++) {
            $dat[$i] =~ s/^\s+|\s+$//g;
        }

        if($dat[0] eq $email) {
            return @dat;
        }
    }

    return undef;
}

sub parse_record {
    my @record = split /\|/, $_[0];
    for (my $i = 0; $i < scalar @record; $i++) {
        $record[$i] =~ s/^\s+|\s+$//g;
    }
    return \@record;
}
    
sub remove_key {
    my $key = $_[0];
    my $fnam = $_[1];
    my $fd;

    open ($fd, '<', $fnam)
        or error 500, "Can't open $fnam.";

    my @dat;
    while (my $x = <$fd>) {
        push @dat, parse_record $x;
    }

    close $fd;

    my $result;

    open ($fd, '>', $fnam)
        or error 500, "Can't open $fnam.";

    for my $x (@dat) {
        if ($x->[2] eq $key) {
            $result = $x;
        }
        else {
            print $fd "$x->[0] | $x->[1] | $x->[2]\n";
        }
    }

    close $fd;
    return $result;
}

my $method = $ENV{"REQUEST_METHOD"};
error(500, "Wrong method")
    if (!defined $method);

if($method eq "POST") {
    my $email = lc(<STDIN>);
    my $name = <STDIN>;

    $email =~ s/^\s+|\s+$//g;
    $name =~ s/^\s+|\s+$//g;

    unless($email and $name) {
        error(400, "Missing email or name (needed 2 lines)");
    }

    unless($email =~ /^[a-zA-Z_0-9.]+@[a-zA-Z_0-9.]+$/) {
        error(400, "$email: wrong email");
    }

    open(my $subfile, '+>>', $subf)
        and open(my $reqfile, '+>>', $reqf)
        or error(500, "Can't touch either: $subf $reqf.");

    if(search_email $subfile, $email) {
        error(400, "$email: already subscribing!");
    }

    if(search_email $reqfile, $email) {
        error(400, "$email: requested subscribtion!");
    }

    my $key = keygen();
    print $reqfile "$email | $name | $key\n";

    print "Status: 200\n\n";

    open(SENDMAIL, "| cat");
    open(TEMPLATE, "<", $template);

    my $link = "$linkbase?$key";

    while (my $l = <TEMPLATE>) {
        $l =~ s/%NAME%/$name/g;
        $l =~ s/%LINK%/$link/g;
        print SENDMAIL $l;
    }


    close(TEMPLATE);
    close(SENDMAIL);

    close($subfile);
    close($reqfile);
}
elsif($method eq "GET") {
    my $key = $ENV{"QUERY_STRING"};
    error(400, "No key given.") unless (defined($key));

    $key = remove_key $key, $reqf;
    
    error(400, "Key not found")
        unless (defined $key);

    open (my $fd, ">>", $subf)
        or error(500, "Can't open $subf");

    print $fd "$key->[0] | $key->[1]\n";

    close $fd;

    print "Status: 200\n\n";
}
else {
    error(400, "Wrong method");
}

