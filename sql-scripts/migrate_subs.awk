BEGIN {
    RS="\n";
    FS="|";
}

{
    sub(/\s*$/, "", $1);
    sub(/^\s*/, "", $2);
    printf("insert into subs (email, name) values ('%s', '%s');\n",
            $1, $2);
}
