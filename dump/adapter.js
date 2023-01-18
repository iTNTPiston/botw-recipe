function count_one_bit(i) {
    assert(i>=0);
    let count = 0;
    while (i > 0){
        if (i & 1){
            count += 1;
        }
        i = i >> 1;
    }
    return count;
}
exports.count_one_bit = count_one_bit;

function to_3_bytes_be(num) {
    const lowest = num & 0xFF;
    const mid = (num >> 8) & 0xFF;
    const hightest = (num >> 16) & 0xFF;
    return [hightest, mid, lowest];
}
exports.to_3_bytes_be = to_3_bytes_be;

function convert_to_record(data) {
    let [base_hp, price, crit_flag, hearty_flag, monster_flag] = data;
    assert(0 <= base_hp <= 120)
    const lower_2_bytes = ((price << 7) + base_hp) & 0xFFFF
    crit_flag = crit_flag ? 1 << 22 : 0;
    hearty_flag = hearty_flag ? 1 << 21 : 0;
    monster_flag = monster_flag ? 1 << 20 : 0;

    const lower_23_bits = lower_2_bytes | crit_flag | hearty_flag | monster_flag;
    // if lower 23 bits has odd number of 1s, set parity bit to 1
    const parity_bit = (count_one_bit(lower_23_bits) & 1) ? 1 << 23 : 0;
    return parity_bit | lower_23_bits
}
exports.convert_to_record = convert_to_record;

function assert(flag){
    if (!flag) {
        throw new Error("AssertionError")
    }
}
exports.assert = assert;