/* Original inspection fixture, intentionally not a complete application. */
extern int write_event(const char *text);
extern int inventory_available(const char *sku);

int reserve(const char *sku, int count) {
    int accepted = 0;
    for (int i = 0; i < count; ++i) {
        if (inventory_available(sku)) {
            if (write_event(sku) != 0) return -1;
            ++accepted;
        }
    }
    return accepted;
}
