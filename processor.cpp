#include <iostream>
#include <libraw/libraw.h>

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input_image.srf> <output_image.ppm|output_image.tiff>\n";
        return 1;
    }

    const char* input_file = argv[1];
    const char* output_file = argv[2];

    // 1. Instantiation
    LibRaw rawProcessor;

    // 2. Open the Sony .srf file and read EXIF/metadata
    int status = rawProcessor.open_file(input_file);
    if (status != LIBRAW_SUCCESS) {
        std::cerr << "Error opening file: " << libraw_strerror(status) << "\n";
        return 1;
    }

    std::cout << "Camera: " << rawProcessor.imgdata.idata.make << " "
              << rawProcessor.imgdata.idata.model << "\n";
    std::cout << "Sensor Dimensions: " << rawProcessor.imgdata.sizes.raw_width 
              << "x" << rawProcessor.imgdata.sizes.raw_height << "\n";

    // 3. Unpack raw Bayer image data into memory
    status = rawProcessor.unpack();
    if (status != LIBRAW_SUCCESS) {
        std::cerr << "Error unpacking RAW data: " << libraw_strerror(status) << "\n";
        rawProcessor.recycle();
        return 1;
    }

    // 4. Configure DCRAW post-processing parameters
    rawProcessor.imgdata.params.use_camera_wb = 1;  // Use embedded camera white balance
    rawProcessor.imgdata.params.output_color = 1;   // Output sRGB color space
    rawProcessor.imgdata.params.output_bps = 8;     // 8 bits per channel (set to 16 for 16-bit TIFF)
    rawProcessor.imgdata.params.user_qual = 3;      // AHD (Adaptive Homogeneity-Directed) demosaicing algorithm

    // 5. Execute demosaicing and color conversion
    status = rawProcessor.dcraw_process();
    if (status != LIBRAW_SUCCESS) {
        std::cerr << "Error during demosaicing: " << libraw_strerror(status) << "\n";
        rawProcessor.recycle();
        return 1;
    }

    // 6. Write processed RGB output file to disk
    status = rawProcessor.dcraw_ppm_tiff_writer(output_file);
    if (status != LIBRAW_SUCCESS) {
        std::cerr << "Error writing output file: " << libraw_strerror(status) << "\n";
        rawProcessor.recycle();
        return 1;
    }

    std::cout << "Successfully exported processed file to: " << output_file << "\n";

    // 7. Cleanup
    rawProcessor.recycle();
    return 0;
}
