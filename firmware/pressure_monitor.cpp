#include "pressure_monitor.hpp"

namespace pf {

State PressureMonitor::update(uint16_t adc) {
    int32_t x = ((static_cast<int32_t>(adc) - cfg_.adc_offset) * cfg_.gain_mN_per_cnt_q8) >> 8;
    if (x < 0) x = 0;
    if (!primed_) { y_ = x; primed_ = true; }
    y_ += static_cast<int32_t>((static_cast<int64_t>(cfg_.alpha_q15) * (x - y_)) >> 15);

    switch (st_) {
    case State::Idle:
        if (y_ >= cfg_.idle_mN) st_ = State::Normal;
        break;
    case State::Normal:
        if (y_ < cfg_.idle_mN) { st_ = State::Idle; cnt_ = 0; break; }
        cnt_ = (y_ >= cfg_.on_mN) ? static_cast<uint16_t>(cnt_ + 1) : 0;
        if (cnt_ >= cfg_.debounce_on) { st_ = State::Overpressure; cnt_ = 0; }
        break;
    case State::Overpressure:
        cnt_ = (y_ < cfg_.off_mN) ? static_cast<uint16_t>(cnt_ + 1) : 0;
        if (cnt_ >= cfg_.debounce_off) { st_ = State::Normal; cnt_ = 0; }
        break;
    }
    return st_;
}

}  // namespace pf
