
setNanoRouteMode -drouteVerboseViolationSummary 1
setNanoRouteMode -routeStripeLayerRange "5:6"
setNanoRouteMode -routeTopRoutingLayer 6
setNanoRouteMode -routeBottomRoutingLayer 2
setNanoRouteMode -routeBottomShieldLayer 3
setNanoRouteMode -droutePostRouteSpreadWire false
setNanoRouteMode -routeWithTimingDriven true
setNanoRouteMode -routeWithSiDriven true
setNanoRouteMode -routeSiEffort high
setNanoRouteMode -routeAllowPinAsFeedthrough true

if {  $stage == "route" } { setNanoRouteMode -drouteUseMultiCutViaEffort low
} else { setNanoRouteMode -drouteUseMultiCutViaEffort high }

setNanoRouteMode -routeStrictlyHonorNonDefaultRule true
setNanoRouteMode -routeReserveSpaceForMultiCut true
setNanoRouteMode -routeConcurrentMinimizeViaCountEffort high
setNanoRouteMode -droutePostRouteSwapVia true
#setNanoRouteMode -drouteFixAntenna true -routeAntennaCellName ANTANMB -routeInsertAntennaDiode true

setNanoRouteMode -dbAdjustAutoViaWeight false

set top_layer [lindex [regexp -all -inline {[0-9]+} [dbGet [dbGet -p1 head.layers.type routing].name ME*]] end]
set direction {"Y" "X"}

set setVx 0
set setVy 0
for {set i 2} {$i <= ${top_layer}} {incr i} {
    set lower_pitch [dbGet [dbGet -p1 [dbGet -p1 head.layers.type routing].name ME[expr ${i} - 1]].pitch[lindex ${direction} [expr [expr ${i} - 1] % 2]]]
    set upper_pitch [dbGet [dbGet -p1 [dbGet -p1 head.layers.type routing].name ME${i}].pitch[lindex ${direction} [expr ${i} % 2]]]
    if { ${upper_pitch} == 0.2 && ${setVy} == 0} {
        puts "### My+1/VIAy"
	puts "setNanoRouteMode -dbViaWeight \"*_FBD_* 5, *_FBS_* 4, *_2cut_P1_* 3, *2cut_P3* 2, *FAT* 1\""
	setNanoRouteMode -dbViaWeight "*_FBD_* 5, *_FBS_* 4, *_2cut_P1_* 3, *2cut_P3* 2, *FAT* 1"
	set setVy 1
    } elseif { ${upper_pitch} == 0.1 && ${setVx} == 0} {
        puts "## Mx+1/VIAx"
	puts "setNanoRouteMode -dbViaWeight \"*_FBD20_* 19, *_FBD30_* 18, *_PBDB_* 17, *_PBDU_* 16, *_PBDE_* 15, *_FBS25_* 4, *_PBSB_* 3, *_PBSU_* 2, *_FAT_* 1\""
	setNanoRouteMode -dbViaWeight "*_FBD20_* 19, *_FBD30_* 18, *_PBDB_* 17, *_PBDU_* 16, *_PBDE_* 15, *_FBS25_* 4, *_PBSB_* 3, *_PBSU_* 2, *_FAT_* 1"
	set setVx 1
    } 
}

