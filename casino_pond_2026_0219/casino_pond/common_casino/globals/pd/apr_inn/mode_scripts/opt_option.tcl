

setOptMode -usefulSkewTNSPreCTS true

setOptMode -allEndPoints true
#setOptMode -enableDataToDataChecks true

setOptMode -clkGateAware true
setOptMode -preserveModuleFunction true

setOptMode -fixDrc true
setOptMode -detailDrvFailureReason true
setOptMode -fixFanoutLoad true
setOptMode -fixSISlew true
setOptMode -areaEffort high

setOptMode -honorFence true

setOptMode -powerEffort low
setOptMode -leakageToDynamicRatio 1

setOptMode -preserveModuleFunction true

setOptMode -reclaimRestructuringEffort high
setOptMode -expExtremeCongestionAwareBuffering true
setOptMode -expReclaimEffort high
setOptMode -reclaimArea true
setOptMode -areaEffort high

setOptMode -usefulSkew $usefulSkew
setOptMode -usefulSkewPreCTS $usefulSkewPreCTS
setOptMode -usefulSkewCCOpt $usefulSkewCCOpt
setOptMode -usefulSkewPostRoute $usefulSkewPostRoute
setUsefulSkewMode -noBoundary true
setUsefulSkewMode -useCells $cts_inverter_cells

setOptMode -fixHoldAllowSetupTnsDegrade false
setOptMode -postRouteAreaReclaim holdAndSetupAware

setOptMode -resizeShifterAndIsoInsts true

setOptMode -verbose true

setOptMode -holdFixingCells "${holdFixingCellList}" 
setOptMode -ignorePathGroupsForHold "in2out in2reg reg2out default"

setOptMode -holdSlackFixingThreshold -2

#setOptMode -autoViewOpt false
#setOptMode -viewOptMustExcludeSetupViewSet
#setOptMode -viewOptMustIncludeHoldViewSet 

