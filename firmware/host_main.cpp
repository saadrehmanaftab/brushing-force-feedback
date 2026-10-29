// Host harness: reads config and ADC samples from stdin, writes one state per line.
// stdin: first line 8 config integers, then one ADC count per line.
#include <cstdio>
#include "pressure_monitor.hpp"

int main() {
    long v[8];
    for (long& x : v) if (std::scanf("%ld", &x) != 1) return 1;
    pf::Config c{(int32_t)v[0], (int32_t)v[1], (int32_t)v[2], (int32_t)v[3], (int32_t)v[4], (int32_t)v[5],
                 (uint16_t)v[6], (uint16_t)v[7]};
    pf::PressureMonitor m(c);
    unsigned adc;
    while (std::scanf("%u", &adc) == 1) std::printf("%d\n", static_cast<int>(m.update(static_cast<uint16_t>(adc))));
    return 0;
}
