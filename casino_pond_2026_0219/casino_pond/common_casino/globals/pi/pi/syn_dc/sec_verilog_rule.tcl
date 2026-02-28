# Samsung verilog namig rule
#******************************************************************************
#** NAMING RULE FOR Verilog HDL: **
#** If you have a plan to layout your chip with Apollo, **
#** you MUST use this naming rule.  **
#**  [1] max_length was removed **
#**  [2] '!' character was allowed for CTS-ed netlist.  **
#******************************************************************************
define_name_rules sec_verilog -type port \
                              -equal_ports_nets  \
                              -allowed {A-Z a-z 0-9 _ [] !} \
                              -first_restricted {0-9 _ !}   \
                              -last_restricted {_ !}

define_name_rules sec_verilog -type cell \
                              -allowed {A-Z a-z 0-9 _ !} \
                              -first_restricted {0-9 _ !} \
                              -last_restricted {_ !} \
                              -map {{{"*-return", "RET"}, {"]$","A"}}}

define_name_rules sec_verilog -type net \
                              -equal_ports_nets \
                              -allowed {A-Z a-z 0-9 _ !} \
                              -first_restricted {0-9 _ !} \
                              -last_restricted {_ !} \
                              -map {{{"*-return", "RET"}, {"]$","A"}}}

