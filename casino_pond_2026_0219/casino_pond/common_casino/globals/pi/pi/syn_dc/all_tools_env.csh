#! /usr/bin/csh -f

# Example stage_n_tool array (replace with actual pairs: stage vendor)
# Cadence Synopsys Ansys Mentor
set stage_n_tool = (\
apr_inn  Cadence \
apr_icc2 Synopsys \
pex      Synopsys \
psi      Ansys \
pv       Mentor \
syn      Synopsys \
dft      Synopsys \
lec      Synopsys \
sta      Synopsys \
dmsa     Synopsys \
sim      Cadence \
)

# Get the current working directory
set CURRENT_DIR = `pwd`

# Loop through the stage_n_tool array (pairs of stage and vendor)
@ i = 1
while ($i <= $#stage_n_tool)
    # Extract the stage and vendor for the current pair
    set stage = $stage_n_tool[$i]
    @ i++
    set vendor = $stage_n_tool[$i]

    # Check if the current directory contains the stage directory
    if ("$CURRENT_DIR" =~ *runs\/*\/$stage) then
        echo "Matching stage found: $stage in $CURRENT_DIR"
        
        # Set environment variables based on the vendor
        switch ($vendor)
            case Ansys:
                echo "Setting environment for Ansys"
                ## Ansys settings
                setenv LM_LICENSE_FILE 25040@lic01
                setenv REDHAWK /mnt/appl/Tools_2024/ansys/Redhwak/V2020_R2.1P
                setenv ARCH amd64
                setenv PATH "${REDHAWK}/bin:$PATH"
                breaksw

            case Mentor:
                echo "Setting environment for Mentor"
                ## Mentor settings
                setenv LM_LICENSE_FILE 25030@lic01
                setenv MEN_CALIBRE /mnt/appl/Tools_2024/mentor/2021.2_28.1/2021.2_28.15P/aoi_cal_2021.2_28.15
                setenv MEN_TESSENT /mnt/appl/Tools/mentor/tessent/tessent_2019_4
                setenv ARCH amd64
                setenv PATH "${MEN_CALIBRE}/bin:${MEN_TESSENT}/bin:$PATH"
                breaksw

            case Cadence:
                echo "Setting environment for Cadence"
                ## Cadence settings
                setenv LM_LICENSE_FILE 25020@lic01
                setenv CDS_LIC_FILE 25020@lic01
                setenv CDS_CONFRMAL /mnt/appl/Tools_2024/cadence/CFML/21.1/CONFRML211/tools.lnx86
                setenv CDS_INNOVUS201 /mnt/appl/Tools/cadence/INNOVUS201/INNOVUS201/tools.lnx86
                setenv CDS_PVS /mnt/appl/Tools/cadence/PVS/PVS191/tools.lnx86
                setenv CDS_SPECTRE /mnt/appl/Tools/cadence/SPECTRE/SPECTRE201/tools.lnx86
                setenv CDS_VOLTUS /mnt/appl/Tools/cadence/ICDSVM/ICDSVM201/tools.lnx86
                setenv CDS_XCELIUM /mnt/appl/Tools/cadence/XCELIUM_Error_EOF/XCELIUM2009/tools.lnx86
                setenv PATH "${CDS_CONFRMAL}/bin:${CDS_INNOVUS201}/bin:${CDS_PVS}/bin:${CDS_SPECTRE}/bin:${CDS_VOLTUS}/bin:$PATH"
                breaksw

            case Synopsys:
                echo "Setting environment for Synopsys"
                ## Synopsys settings
                setenv LM_LICENSE_FILE 25010@lic01
                setenv SNPSLMD_LICENSE_FILE 25010@lic01
                setenv SYN_DC /mnt/appl/Tools_2024/synopsys/syn/S-2021.06-SP4P/
                setenv SYN_FORMALITY /mnt/appl/Tools_2024/synopsys/fm/S-2021.06-SP4P
                setenv SYN_ICC2 /mnt/appl/Tools_2024/synopsys/icc2/S-2021.06-SP4P
                setenv SYN_PT /mnt/appl/Tools_2024/synopsys/prime/S-2021.06-SP4P
                setenv SYN_STARRCXT /mnt/appl/Tools_2024/synopsys/starrc/S-2021.06-SP4P
                setenv SYN_TMAX /mnt/appl/Tools_2024/synopsys/txs/S-2021.06-SP4P
                setenv SYN_LC /mnt/appl/Tools_2024/synopsys/lc/S-2021.06-SP4P
                setenv SYN_TESTMAX /mnt/appl/Tools_2024/synopsys/testmax/S-2021.06-SP3P
                setenv SYN_VERDI /mnt/appl/Tools_2024/synopsys/verdi/S-2021.09-SP1P
                setenv PATH "${SYN_DC}/bin:${SYN_FORMALITY}/bin:${SYN_ICC2}/bin:${SYN_PT}/bin:${SYN_STARRCXT}/bin:${SYN_TMAX}/bin:${SYN_LC}/bin:${SYN_TESTMAX}/bin:${SYN_VERDI}/bin:$PATH"
                breaksw

            default:
                echo "Unknown vendor: $vendor"
                breaksw
        endsw

        # Exit the loop since we've found the matching stage directory
        break
    endif

    @ i++
end

