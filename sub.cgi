#!/usr/bin/env perl

use strict;
use warnings;
use Encode;
use utf8;
use DBI;

my $template = 'confirm-msg.html';
my $notiftemp = 'sub-notif.html';
my $succmsg = 'success-msg.html';
my $msmsg = 'mail-sent-msg.html';
my $linkbase = "http://???/cgi-bin/sub.cgi";
my $submail = '???';
my $admail = '???';
my $subtitle = 'Proszę, potwierdź subskrybcję.';
my $notiftitle = 'Masz nowego subskrybenta.';
my $dbsn = 'DBI:mysql:database=???:host=localhost';
my $dbusr = '???';
my $dbpass = '???';

my $db = DBI->connect($dbsn, $dbusr, $dbpass) or error(400, "Internal error: connect db");

sub error {
    my ($status, $msg) = @_;
    print("Status: $status\n\n$msg\n");
    $db->disconnect();
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
    my ($tab, $email) = @_;
    my $req = $db->prepare("select * from $tab where email=?");
    $req->execute($email) or error (400, "Internal error: se $tab, $email\n" .
                                               $db->errstr);
    while(my $ref = $req->fetchrow_hashref()) {
        if($ref->{'email'} eq $email) {
            return $ref;
        }

        return undef;
    }
}

sub remove_key {
    my ($hash, $tab) = @_;
    my $req = $db->prepare("select * from $tab where hash=?");
    $req->execute($hash) or error(400, "Internal error: rk $tab, $hash\n" .
                                        $db->errstr);
    if (my $ref = $req->fetchrow_hashref()) {
        $req = $db->prepare("delete from $tab where hash=?");
        $req->execute($hash);
        return $ref;
    }

    return undef;
}

sub get_params {
    my $src = $_[0];
    $src =~ s/%([[:xdigit:]]{2})/chr(hex $1)/ge;
    $src =~ s/\+/ /g;
    chomp $src;

    my %result;
    for my $keyval (split /&/, $src) {
        my ($key, $val) = split /=/, $keyval;
        $result{$key} = $val;
    }

    return \%result;
}

sub rewrite {
    print "Status: 200\n\n";

    my $smsg;
    if(!open($smsg, '<', $_[0])) {
        print "Subscription accepted.";
	    exit;
    }

    while(my $l = <$smsg>) {
        print $l;
    }
}

sub sendmail {
    my ($submail, $email, $subtitle, $template, $subsf) = @_, 
    $subtitle = encode("MIME-Q", $subtitle);
    open(SENDMAIL, "| mail -a 'Content-type:text/html; charset=UTF-8' -r $submail -s '$subtitle' $email");
    open(TEMPLATE, "<", $template);

    while (my $l = <TEMPLATE>) {
        print SENDMAIL &$subsf($l);
    }


    close(TEMPLATE);
    close(SENDMAIL);
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
    my $message = $params->{"msg"};

    unless($email =~ /^[a-zA-Z_0-9.]+@[a-zA-Z_0-9.]+$/) {
        error(400, "$email: wrong email");
    }

    if(search_email("subs", $email)) {
        error(400, "$email: already subscribing!");
    }

    if(search_email("subreq", $email)) {
        error(400, "$email: requested subscribtion!");
    }

    my $key = keygen();
    my $req = $db->prepare("insert into subreq (email, name, hash) values(?,?,?)");
    $req->execute($email, $name, $key) or error(400, "Internal error, try again");

    rewrite $msmsg;

    my $link = "$linkbase?$key";

    sendmail($submail, $email, $subtitle, $template, 
        sub {
            my ($l) = @_;
            $l =~ s/%NAME%/$name/g;
            $l =~ s/%LINK%/$link/g;
            return $l;
        }
    );

    sendmail($submail, $admail, $notiftitle, $notiftemp,
        sub {
            my ($l) = @_;
            $l =~ s/%NAME%/$name/g;
            $l =~ s/%EMAIL%/$email/g;
	    $l =~ s/%MSG%/$message/g;
            return $l;
        }
    );
}
elsif($method eq "GET") {
    my $key = $ENV{"QUERY_STRING"};
    error(400, "No key given.") unless (defined($key));

    $key = remove_key $key, "subreq";
    
    error(400, "Key not found")
        unless (defined $key);

    my $req = $db->prepare("insert into subs (email,name) values(?,?)");
    $req->execute($key->{"email"}, $key->{"name"});

    rewrite $succmsg;
}
else {
    error(400, "Wrong method");
}

$db->disconnect();
