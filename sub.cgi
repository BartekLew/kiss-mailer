#!/usr/bin/env perl

use strict;
use warnings;
use Encode;
use utf8;

my $subf = 'subs.dat';
my $reqf = 'req.dat';
my $template = 'confirm-msg.html';
my $succmsg = 'success-msg.html';
my $linkbase = "http://it.wiedz.net.pl/cgi-bin/sub.cgi";
my $submail = 'mailer@wiedz.net.pl';
my $subtitle = 'Proszę, potwierdź subskrybcję.';

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

sub get_params {
    my $src = $_[0];
    $src =~ s/%([[:xdigit:]]{2})/chr(hex $1)/e;
    chomp $src;

    my %result;
    for my $keyval (split /&/, $src) {
        my ($key, $val) = split /=/, $keyval;
        $result{$key} = $val;
    }

    return \%result;
}

my $method = $ENV{"REQUEST_METHOD"};
error(500, "Wrong method")
    if (!defined $method);

if($method eq "POST") {
    my $params = get_params(<STDIN>);
    
    unless($params->{"email"} and $params->{"name"}) {
        error(400, "Missing email or name param");
    }

    my $email = lc($params->{"email"});
    my $name = $params->{"name"};

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

    $subtitle = encode("MIME-Q", $subtitle);
    open(SENDMAIL, "| mail -a 'Content-type:text/html; charset=UTF-8' -r $submail -s '$subtitle' $email");
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

    my $smsg;
    if(!open($smsg, '<', $succmsg)) {
        print "Subscription accepted.";
	exit;
    }

    while(my $l = <$smsg>) {
        print $l;
    }
}
else {
    error(400, "Wrong method");
}

