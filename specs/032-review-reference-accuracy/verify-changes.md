# Changed review points 2.9.0 -> 032 (snapshot copies, 2026-11-11)

Reason per change: own-net via clearance -> not reported; other-net via clearance -> INFO 'Trace over via clearance'; SOV twins of a Loss of reference stretch -> merged into the one LoR / removed; no-net padstack voids (mechanical holes) stay real gaps (PCIe 3 LoR HIGH kept).

```
== serlink SERLINK_U14_U15: items 47 -> 52; changed counts {'Trace over via clearance INFO': (0, 5)}
   + added   INFO Trace over via clearance SERLINK_DEVA2DEVB_L1_N Layer 3 ref Layer 2 - GND (212.7054, 66.6384) in the clearance of 1 via(s) of SERLINK_DEVA2DEVB_L1_P on Layer 2 - GND; void up to 1.15 x 1.95 mm over 1.000 mm
   + added   INFO Trace over via clearance SERLINK_DEVA2DEVB_L1_N* Layer 3 ref Layer 2 - GND (101.3372, 67.9946) in the clearance of 1 via(s) of SERLINK_DEVA2DEVB_L1_P* on Layer 2 - GND; void up to 1.95 x 1.15 mm over 0.950 mm
   + added   INFO Trace over via clearance SERLINK_DEVA2DEVB_L1_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (108.6383, 64.7707) in the clearance of 1 via(s) of P1V2_MIPI01_A on Layer 2 - GND, Layer 4 - GND; void up to 1.80 x 1.90 mm over 0.050 mm
   + added   INFO Trace over via clearance SERLINK_DEVB2DEVA_L1_N Layer 3 ref Layer 2 - GND (95.2054, 66.6616) in the clearance of 1 via(s) of SERLINK_DEVB2DEVA_L1_P on Layer 2 - GND; void up to 1.15 x 1.95 mm over 0.950 mm
   + added   INFO Trace over via clearance SERLINK_DEVB2DEVA_L1_N* Layer 3 ref Layer 2 - GND (218.8615, 67.9946) in the clearance of 1 via(s) of SERLINK_DEVB2DEVA_L1_P* on Layer 2 - GND; void up to 1.95 x 1.15 mm over 1.000 mm
== serlink SERLINK_U14_J8: items 57 -> 24; changed counts {'Loss of reference HIGH': (12, 0), 'SOV MEDIUM': (24, 0), 'Trace over via clearance INFO': (0, 3)}
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (126.3906, 138.0804) no GND over 1.550 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (127.9246, 133.2841) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (127.9246, 134.0167) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (125.6094, 138.0812) no GND over 1.550 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (127.6254, 133.2844) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (127.6254, 134.0174) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (134.3906, 138.0843) no GND over 1.550 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (134.4996, 134.8342) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND, Layer 4 - GND (134.4996, 135.5653) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (133.6094, 138.0851) no GND over 1.550 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (134.2004, 134.837) no GND over 0.350 mm
   - removed HIGH Loss of reference SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (134.2004, 135.5656) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND (126.3906, 138.0804) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND (127.9246, 133.2841) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND (127.9246, 134.0167) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 4 - GND (126.3906, 138.0804) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 4 - GND (127.9246, 133.2841) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 4 - GND (127.9246, 134.0167) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND (125.6094, 138.0812) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND (127.6254, 133.2844) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND (127.6254, 134.0174) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 4 - GND (125.6094, 138.0812) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 4 - GND (127.6254, 133.2844) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 4 - GND (127.6254, 134.0174) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND (134.3906, 138.0843) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND (134.4996, 134.8342) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 2 - GND (134.4996, 135.5653) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 4 - GND (134.3906, 138.0843) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 4 - GND (134.4996, 134.8342) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_N Layer 3 ref Layer 4 - GND (134.4996, 135.5653) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND (133.6094, 138.0851) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND (134.2004, 134.837) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 2 - GND (134.2004, 135.5656) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 4 - GND (133.6094, 138.0851) no GND over 1.550 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 4 - GND (134.2004, 134.837) no GND over 0.350 mm
   - removed MEDIUM SOV SERLINK_M2M_AC_TX_L3_P Layer 3 ref Layer 4 - GND (134.2004, 135.5656) no GND over 0.350 mm
   + added   INFO Trace over via clearance SERLINK_M2M_AC_TX_L2_N Layer 3 ref Layer 2 - GND (108.6347, 70.5137) in the clearance of 1 via(s) of P0V75_VDDMIPI23_A on Layer 2 - GND; void up to 1.80 x 1.90 mm over 0.050 mm
   + added   INFO Trace over via clearance SERLINK_M2M_AC_TX_L2_P Layer 3 ref Layer 2 - GND (108.6347, 70.9333) in the clearance of 1 via(s) of P0V75_VDDMIPI23_A on Layer 2 - GND; void up to 1.80 x 1.90 mm over 0.050 mm
   + added   INFO Trace over via clearance SERLINK_M2M_AC_TX_L3_P* Layer 3 ref Layer 2 - GND (101.3341, 70.2109) in the clearance of 1 via(s) of SERLINK_M2M_AC_TX_L3_N* on Layer 2 - GND; void up to 1.95 x 1.15 mm over 1.000 mm
== serlink SERLINK_U14_U227: items 12 -> 13; changed counts {'Trace over via clearance INFO': (0, 1)}
   + added   INFO Trace over via clearance SERLINK_M2M_AC_RX_L3_RDV_P Layer 9 ref Layer 8 - GND, Layer 10 - GND (96.1824, 67.0076) in the clearance of 1 via(s) of SERLINK_M2M_AC_RX_L3_RDV_N on Layer 8 - GND, Layer 10 - GND; void up to 0.70 x 1.50 mm over 0.200 mm
== pcie PCIE_U14_J25: items 103 -> 69; changed counts {'Loss of reference HIGH': (19, 3), 'SOV MEDIUM': (38, 0), 'Trace over via clearance INFO': (0, 20)}
   - removed HIGH Loss of reference PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (118.956, 58.3843) no GND over 0.100 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (123.0229, 63.0409) no GND over 0.150 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (126.7438, 32.2786) no GND over 0.250 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (115.0261, 82.931) no GND over 0.150 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (119.6706, 79.7114) no GND over 0.150 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (131.8851, 23.8483) no GND over 0.300 mm
   - removed HIGH Loss of reference PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (134.7757, 21.9068) no GND over 0.050 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (116.8607, 44.8293) no GND over 0.400 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (117.4928, 65.7777) no GND over 0.450 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (114.9031, 74.9921) no GND over 0.200 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (117.4821, 74.53) no GND over 0.350 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (118.7215, 43.9879) no GND over 0.300 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (120.1022, 36.3397) no GND over 0.350 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (121.999, 31.9588) no GND over 0.600 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (121.072, 34.1322) no GND over 0.450 mm
   - removed HIGH Loss of reference PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (123.7298, 27.6246) no GND over 0.250 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND (118.956, 58.3843) no GND over 0.100 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND (134.4419, 19.3938) no GND over 1.500 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_N Layer 14 ref Layer 15 - GND (118.956, 58.3843) no GND over 0.100 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_N Layer 14 ref Layer 15 - GND (134.4419, 19.3938) no GND over 1.500 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_P Layer 14 ref Layer 13 - GND (134.2736, 19.2311) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L0_P Layer 14 ref Layer 15 - GND (134.2736, 19.2311) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND (123.0229, 63.0409) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND (126.7438, 32.2786) no GND over 0.250 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND (135.6835, 21.0524) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 15 - GND (123.0229, 63.0409) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 15 - GND (126.7438, 32.2786) no GND over 0.250 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_N Layer 14 ref Layer 15 - GND (135.6835, 21.0524) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND (115.0261, 82.931) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND (119.6706, 79.7114) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND (131.8851, 23.8483) no GND over 0.300 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND (134.7757, 21.9068) no GND over 0.050 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 15 - GND (115.0261, 82.931) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 15 - GND (119.6706, 79.7114) no GND over 0.150 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 15 - GND (131.8851, 23.8483) no GND over 0.300 mm
   - removed MEDIUM SOV PCIE_HSA2HSB_L1_P Layer 14 ref Layer 15 - GND (134.7757, 21.9068) no GND over 0.050 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND (116.8607, 44.8293) no GND over 0.400 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND (117.4928, 65.7777) no GND over 0.450 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L0_P Layer 14 ref Layer 15 - GND (116.8607, 44.8293) no GND over 0.400 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L0_P Layer 14 ref Layer 15 - GND (117.4928, 65.7777) no GND over 0.450 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND (114.9031, 74.9921) no GND over 0.200 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND (117.4821, 74.53) no GND over 0.350 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND (118.7215, 43.9879) no GND over 0.300 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND (120.1022, 36.3397) no GND over 0.350 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND (121.999, 31.9588) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 15 - GND (114.9031, 74.9921) no GND over 0.200 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 15 - GND (117.4821, 74.53) no GND over 0.350 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 15 - GND (118.7215, 43.9879) no GND over 0.300 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 15 - GND (120.1022, 36.3397) no GND over 0.350 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_N Layer 14 ref Layer 15 - GND (121.999, 31.9588) no GND over 0.600 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND (121.072, 34.1322) no GND over 0.450 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND (123.7298, 27.6246) no GND over 0.250 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_P Layer 14 ref Layer 15 - GND (121.072, 34.1322) no GND over 0.450 mm
   - removed MEDIUM SOV PCIE_HSB2HSA_L1_P Layer 14 ref Layer 15 - GND (123.7298, 27.6246) no GND over 0.250 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (118.956, 58.3843) in the clearance of 1 via(s) of I2C_DEVA2DESERA0_SCL on Layer 13 - GND, Layer 15 - GND; void up to 1.35 x 0.76 mm over 0.100 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L0_N* Layer 3 ref Layer 2 - GND (101.3457, 81.4161) in the clearance of 1 via(s) of PCIE_HSA2HSB_L0_P* on Layer 2 - GND; void up to 1.95 x 1.15 mm over 1.000 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (123.0229, 63.0409) in the clearance of 1 via(s) of P1V2_SOC_AVDDMIPI_VDDIOUFS_A on Layer 13 - GND, Layer 15 - GND; void up to 1.38 x 0.65 mm over 0.150 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (126.7438, 32.2786) in the clearance of 1 via(s) of PWR_OUT_TRUNK/RL_PASS on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.250 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_N* Layer 3 ref Layer 2 - GND (101.3412, 82.3946) in the clearance of 1 via(s) of PCIE_HSA2HSB_L1_P* on Layer 2 - GND; void up to 1.95 x 1.15 mm over 0.950 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (115.0261, 82.931) in the clearance of 1 via(s) of P0V75_PCIe_CLK_A on Layer 13 - GND, Layer 15 - GND; void up to 1.35 x 0.65 mm over 0.150 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (119.6706, 79.7114) in the clearance of 1 via(s) of P1V8_SOC_A on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 1.22 mm over 0.150 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (131.8851, 23.8483) in the clearance of 1 via(s) of EN_LC_CAM_PWR_HSB_BUF on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.300 mm
   + added   INFO Trace over via clearance PCIE_HSA2HSB_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (134.7757, 21.9068) in the clearance of 1 via(s) of ERR_LC2HSB_B2B on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.050 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (98.5815, 79.9528) in the clearance of 1 via(s) of PCIE_HSB2HSA_L0_N on Layer 13 - GND, Layer 15 - GND; void up to 1.45 x 0.65 mm over 0.150 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (116.8607, 44.8293) in the clearance of 1 via(s) of P1V8_DESER_A on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.400 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (117.4928, 65.7777) in the clearance of 1 via(s) of P0V75_HSIO_DVDD_A on Layer 13 - GND, Layer 15 - GND; void up to 1.33 x 0.65 mm over 0.450 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (114.9031, 74.9921) in the clearance of 1 via(s) of P0V75_ETH10G_CLK_A on Layer 13 - GND, Layer 15 - GND; void up to 1.35 x 0.65 mm over 0.200 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (117.4821, 74.53) in the clearance of 1 via(s) of P0V75_HSIO_AVDD_A on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 1.37 mm over 0.350 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (118.7215, 43.9879) in the clearance of 1 via(s) of FSYNC_LC_X2A on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.300 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (120.1022, 36.3397) in the clearance of 1 via(s) of P1V8_RSI_A on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.350 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (121.999, 31.9588) in the clearance of 1 via(s) of PWR_OUT_FRONT_NAR/RR_PASS on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.600 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (98.5815, 82.2473) in the clearance of 1 via(s) of PCIE_HSB2HSA_L1_N on Layer 13 - GND, Layer 15 - GND; void up to 1.45 x 0.65 mm over 0.150 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (121.072, 34.1322) in the clearance of 1 via(s) of P1V8_HSB on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.450 mm
   + added   INFO Trace over via clearance PCIE_HSB2HSA_L1_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (123.7298, 27.6246) in the clearance of 1 via(s) of NetC2399_2 on Layer 13 - GND, Layer 15 - GND; void up to 0.65 x 0.65 mm over 0.250 mm
== board1 CPHY_U14_U26: items 27 -> 27; changed counts {}
== board1 CPHY_U21_J25: items 32 -> 32; changed counts {}
```

## Plane edge: one finding per stretch (user "Gộp", 2026-11-11)

Counts vs the first 032 run: SERLINK U14_U15 Near plane edge 4 -> 2, U14_U227 2 -> 1; PCIe 6 -> 3 (items 69 -> 66, reference 5 / 16 / 45, points 5 / 13 unchanged); board1 CPHY_U14_U26 2 -> 1, CPHY_U21_J25 2 -> 1. Each removed row was the second plane of the same stretch, now listed inside the one finding.

```
== serlink SERLINK_U14_U15: items 52 -> 50; changed counts {'Near plane edge MEDIUM': (4, 2)}
   - removed MEDIUM Near plane edge SERLINK_DEVA2DEVB_L1_P Layer 3 ref Layer 2 - GND (207.9049, 47.779) GND edge on Layer 2 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 0.600 mm in total (longest 0.600 mm)
   - removed MEDIUM Near plane edge SERLINK_DEVA2DEVB_L1_P Layer 3 ref Layer 4 - GND (207.9049, 47.779) GND edge on Layer 4 - GND within 0.291 mm of the trace centre (H 0.097 mm) on 1 stretch(es), 0.600 mm in total (longest 0.600 mm)
   - removed MEDIUM Near plane edge SERLINK_DEVB2DEVA_L1_P Layer 3 ref Layer 2 - GND (165.5044, 57.4968) GND edge on Layer 2 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 2.100 mm in total (longest 2.100 mm)
   - removed MEDIUM Near plane edge SERLINK_DEVB2DEVA_L1_P Layer 3 ref Layer 4 - GND (165.5044, 57.4968) GND edge on Layer 4 - GND within 0.291 mm of the trace centre (H 0.097 mm) on 1 stretch(es), 2.000 mm in total (longest 2.000 mm)
   + added   MEDIUM Near plane edge SERLINK_DEVA2DEVB_L1_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (207.9049, 47.779) GND edge within Layer 2 - GND 0.306 mm (H 0.102 mm); Layer 4 - GND 0.291 mm (H 0.097 mm) of the trace centre on 1 stretch(es), 0.600 mm in total (longest 0.600 mm)
   + added   MEDIUM Near plane edge SERLINK_DEVB2DEVA_L1_P Layer 3 ref Layer 2 - GND, Layer 4 - GND (165.5044, 57.4968) GND edge within Layer 2 - GND 0.306 mm (H 0.102 mm); Layer 4 - GND 0.291 mm (H 0.097 mm) of the trace centre on 1 stretch(es), 2.100 mm in total (longest 2.100 mm)
== serlink SERLINK_U14_J8: items 24 -> 24; changed counts {}
== serlink SERLINK_U14_U227: items 13 -> 12; changed counts {'Near plane edge MEDIUM': (2, 1)}
   - removed MEDIUM Near plane edge SERLINK_M2M_AC_RX_L2_RDV_P Layer 9 ref Layer 10 - GND (127.45, 89.5698) GND edge on Layer 10 - GND within 0.288 mm of the trace centre (H 0.096 mm) on 2 stretch(es), 1.200 mm in total (longest 0.600 mm)
   - removed MEDIUM Near plane edge SERLINK_M2M_AC_RX_L2_RDV_P Layer 9 ref Layer 8 - GND (127.45, 89.1936) GND edge on Layer 8 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 1.350 mm in total (longest 1.350 mm)
   + added   MEDIUM Near plane edge SERLINK_M2M_AC_RX_L2_RDV_P Layer 9 ref Layer 8 - GND, Layer 10 - GND (127.45, 89.1936) GND edge within Layer 8 - GND 0.306 mm (H 0.102 mm); Layer 10 - GND 0.288 mm (H 0.096 mm) of the trace centre on 1 stretch(es), 1.350 mm in total (longest 1.350 mm)
== pcie PCIE_U14_J25: items 69 -> 66; changed counts {'Near plane edge MEDIUM': (6, 3)}
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND (135.4009, 18.8185) GND edge on Layer 13 - GND within 0.297 mm of the trace centre (H 0.099 mm) on 1 stretch(es), 0.750 mm in total (longest 0.750 mm)
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L0_N Layer 14 ref Layer 15 - GND (135.4009, 18.8185) GND edge on Layer 15 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 0.750 mm in total (longest 0.750 mm)
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L0_P Layer 14 ref Layer 13 - GND (134.2736, 19.2311) GND edge on Layer 13 - GND within 0.297 mm of the trace centre (H 0.099 mm) on 1 stretch(es), 1.500 mm in total (longest 1.500 mm)
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L0_P Layer 14 ref Layer 15 - GND (134.2913, 19.2134) GND edge on Layer 15 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 1.550 mm in total (longest 1.550 mm)
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND (135.6835, 21.0524) GND edge on Layer 13 - GND within 0.297 mm of the trace centre (H 0.099 mm) on 2 stretch(es), 1.400 mm in total (longest 0.900 mm)
   - removed MEDIUM Near plane edge PCIE_HSA2HSB_L1_N Layer 14 ref Layer 15 - GND (135.6835, 21.0524) GND edge on Layer 15 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 2 stretch(es), 1.400 mm in total (longest 0.900 mm)
   + added   MEDIUM Near plane edge PCIE_HSA2HSB_L0_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (135.4009, 18.8185) GND edge within Layer 13 - GND 0.297 mm (H 0.099 mm); Layer 15 - GND 0.306 mm (H 0.102 mm) of the trace centre on 1 stretch(es), 0.750 mm in total (longest 0.750 mm)
   + added   MEDIUM Near plane edge PCIE_HSA2HSB_L0_P Layer 14 ref Layer 13 - GND, Layer 15 - GND (134.2913, 19.2134) GND edge within Layer 13 - GND 0.297 mm (H 0.099 mm); Layer 15 - GND 0.306 mm (H 0.102 mm) of the trace centre on 1 stretch(es), 1.550 mm in total (longest 1.550 mm)
   + added   MEDIUM Near plane edge PCIE_HSA2HSB_L1_N Layer 14 ref Layer 13 - GND, Layer 15 - GND (135.6835, 21.0524) GND edge within Layer 13 - GND 0.297 mm (H 0.099 mm); Layer 15 - GND 0.306 mm (H 0.102 mm) of the trace centre on 2 stretch(es), 1.400 mm in total (longest 0.900 mm)
== board1 CPHY_U14_U26: items 27 -> 26; changed counts {'Near plane edge MEDIUM': (2, 1)}
   - removed MEDIUM Near plane edge CPHY_B02DEVA_L1_A Layer 3 ref Layer 2 - GND (101.9868, 50.0) GND edge on Layer 2 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 2.050 mm in total (longest 2.050 mm)
   - removed MEDIUM Near plane edge CPHY_B02DEVA_L1_A Layer 3 ref Layer 4 - GND (102.012, 50.0) GND edge on Layer 4 - GND within 0.372 mm of the trace centre (H 0.124 mm) on 1 stretch(es), 2.300 mm in total (longest 2.300 mm)
   + added   MEDIUM Near plane edge CPHY_B02DEVA_L1_A Layer 3 ref Layer 2 - GND, Layer 4 - GND (102.012, 50.0) GND edge within Layer 2 - GND 0.306 mm (H 0.102 mm); Layer 4 - GND 0.372 mm (H 0.124 mm) of the trace centre on 1 stretch(es), 2.300 mm in total (longest 2.300 mm)
== board1 CPHY_U21_J25: items 32 -> 31; changed counts {'Near plane edge MEDIUM': (2, 1)}
   - removed MEDIUM Near plane edge CPHY_LC2HSB_L2_C Layer 5 ref Layer 4 - GND (107.7577, 22.1788) GND edge on Layer 4 - GND within 0.306 mm of the trace centre (H 0.102 mm) on 1 stretch(es), 6.550 mm in total (longest 6.550 mm)
   - removed MEDIUM Near plane edge CPHY_LC2HSB_L2_C Layer 5 ref Layer 6 - GND (107.7577, 22.2291) GND edge on Layer 6 - GND within 0.366 mm of the trace centre (H 0.122 mm) on 1 stretch(es), 6.650 mm in total (longest 6.650 mm)
   + added   MEDIUM Near plane edge CPHY_LC2HSB_L2_C Layer 5 ref Layer 4 - GND, Layer 6 - GND (107.7577, 22.2291) GND edge within Layer 4 - GND 0.306 mm (H 0.102 mm); Layer 6 - GND 0.366 mm (H 0.122 mm) of the trace centre on 1 stretch(es), 6.650 mm in total (longest 6.650 mm)
```
