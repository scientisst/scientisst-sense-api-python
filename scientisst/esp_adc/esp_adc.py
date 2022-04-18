from scientisst.esp_adc.constants import *
from scientisst.esp_adc.lut_adc import *


class EspAdcCalChars:
    def __init__(self, buffer):
        self.adc_num = int.from_bytes(buffer[0:4], "little")
        self.atten = int.from_bytes(buffer[4:8], "little")
        self.bit_width = int.from_bytes(buffer[8:12], "little")
        self.coeff_a = int.from_bytes(buffer[12:16], "little")
        self.coeff_b = int.from_bytes(buffer[16:20], "little")
        self.vref = int.from_bytes(buffer[20:24], "little")

        # Initialize fields for lookup table if necessary
        if self.atten == ADC_ATTEN_DB_11:
            if self.adc_num == ADC_UNIT_1:
                self.low_curve = LUT_ADC1_LOW
            else:
                self.low_curve = LUT_ADC2_LOW

            if self.adc_num == ADC_UNIT_1:
                self.high_curve = LUT_ADC1_HIGH
            else:
                self.high_curve = LUT_ADC2_HIGH
        else:
            self.low_curve = 0
            self.high_curve = 0

    def esp_adc_cal_raw_to_voltage(self, adc_reading):
        adc_reading = adc_reading << (ADC_WIDTH_BIT_12 - self.bit_width)
        if adc_reading > ADC_12_BIT_RES - 1:
            adc_reading = ADC_12_BIT_RES - 1

        if self.atten == ADC_ATTEN_DB_11 and adc_reading >= LUT_LOW_THRESH:
            #
            lut_voltage = EspAdcCalChars.calculate_voltage_lut(
                adc_reading, self.vref, self.low_curve, self.high_curve
            )

            if adc_reading <= LUT_HIGH_THRESH:
                linear_voltage = EspAdcCalChars.calculate_voltage_linear(
                    adc_reading, self.coeff_a, self.coeff_b
                )

                voltage = EspAdcCalChars.interpolate_two_points(
                    linear_voltage,
                    lut_voltage,
                    LUT_ADC_STEP_SIZE,
                    (adc_reading - LUT_LOW_THRESH),
                )
            else:
                voltage = lut_voltage
        else:
            voltage = EspAdcCalChars.calculate_voltage_linear(
                adc_reading, self.coeff_a, self.coeff_b
            )

        return int(voltage * VOLT_DIVIDER_FACTOR)

    def interpolate_two_points(y1, y2, x_step, x):
        # Interpolate between two points (x1,y1) (x2,y2) between 'lower' and 'upper' separated by 'step'
        return int(((y1 * x_step) + (y2 * x) - (y1 * x) + int(x_step / 2)) / x_step)

    def calculate_voltage_linear(adc_reading, coeff_a, coeff_b):
        # Where voltage = coeff_a * adc_reading + coeff_b
        return (
            int(((coeff_a * adc_reading) + LIN_COEFF_A_ROUND) / LIN_COEFF_A_SCALE)
            + coeff_b
        )

    def calculate_voltage_lut(adc, vref, low_vref_curve, high_vref_curve):

        # Get index of lower bound points of LUT
        i = int((adc - LUT_LOW_THRESH) / LUT_ADC_STEP_SIZE)

        # Let the X Axis be Vref, Y axis be ADC reading, and Z be voltage
        x2dist = LUT_VREF_HIGH - vref  # (x2 - x)
        x1dist = vref - LUT_VREF_LOW  # (x - x1)
        y2dist = ((i + 1) * LUT_ADC_STEP_SIZE) + LUT_LOW_THRESH - adc  # (y2 - y)
        y1dist = adc - ((i * LUT_ADC_STEP_SIZE) + LUT_LOW_THRESH)  # (y - y1)

        # For points for bilinear interpolation
        q11 = low_vref_curve[i]  # Lower bound point of low_vref_curve
        q12 = low_vref_curve[i + 1]  # Upper bound point of low_vref_curve
        q21 = high_vref_curve[i]  # Lower bound point of high_vref_curve
        q22 = high_vref_curve[i + 1]  # Upper bound point of high_vref_curve

        # Bilinear interpolation
        # Where z = 1/((x2-x1)*(y2-y1)) * ( (q11*x2dist*y2dist) + (q21*x1dist*y2dist) + (q12*x2dist*y1dist) + (q22*x1dist*y1dist) )
        voltage = (
            (q11 * x2dist * y2dist)
            + (q21 * x1dist * y2dist)
            + (q12 * x2dist * y1dist)
            + (q22 * x1dist * y1dist)
        )
        voltage += int(((LUT_VREF_HIGH - LUT_VREF_LOW) * LUT_ADC_STEP_SIZE) / 2)
        # Integer division rounding
        voltage = int(voltage / (LUT_VREF_HIGH - LUT_VREF_LOW) * LUT_ADC_STEP_SIZE)
        # Divide by ((x2-x1)*(y2-y1))

        return voltage
