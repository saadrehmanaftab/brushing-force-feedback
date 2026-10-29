// Brushing force feedback logic for a smart consumer device (personal project, assumed data).
// Embedded style: fixed point integer math, no heap, no exceptions, one call per sensor sample.
#pragma once
#include <cstdint>

namespace pf {

enum class State : uint8_t { Idle = 0, Normal = 1, Overpressure = 2 };

struct Config {
    int32_t adc_offset;        // ADC counts at zero force
    int32_t gain_mN_per_cnt_q8;// force per ADC count in mN, Q8 fixed point
    int32_t alpha_q15;         // IIR low pass coefficient, Q15
    int32_t on_mN;             // force that starts the over pressure warning
    int32_t off_mN;            // force that ends it (hysteresis, off < on)
    int32_t idle_mN;           // below this the head is not on the teeth
    uint16_t debounce_on;      // samples above on_mN before the warning is raised
    uint16_t debounce_off;     // samples below off_mN before it is cleared
};

class PressureMonitor {
public:
    explicit PressureMonitor(const Config& c) : cfg_(c) {}
    State update(uint16_t adc);          // call at the sensor rate
    int32_t filtered_mN() const { return y_; }
    State state() const { return st_; }
private:
    Config cfg_;
    int32_t y_ = 0;                      // filtered force, mN
    bool primed_ = false;
    uint16_t cnt_ = 0;
    State st_ = State::Idle;
};

}  // namespace pf
