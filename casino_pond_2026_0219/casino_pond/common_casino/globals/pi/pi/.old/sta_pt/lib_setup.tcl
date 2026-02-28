echo "INFO : SOURCE [info script]"

set_app_var link_library [list *]

set std_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/std/db/${pvt_corner}/*]
foreach lib $std_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set mem_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/mem/db/${pvt_corner}/*]
foreach lib $mem_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

set io_ip_list [glob -nocomplain -type f ${DB_PATH}/vers/${db_ver}/io_ip/db/${pvt_corner}/*]
foreach lib $io_ip_list {
    echo "link_library : $lib"
	lappend link_library $lib
}

