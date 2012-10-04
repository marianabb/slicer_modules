#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkWarpImageFilter.h"
//#include "itkRescaleIntensityImageFilter.h"

#include "WarpVolumeCLP.h"

typedef float PixelType;
typedef float OutPixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType;
typedef itk::Image< OutPixelType, Dimension > OutImageType;

typedef float VectorComponentType;
typedef itk::Vector< VectorComponentType, Dimension >    VectorType;
typedef itk::Image< VectorType,  Dimension >   DFImageType;

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileReader< DFImageType > DFReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;
typedef itk::ImageFileWriter< OutImageType > OutWriterType;

//typedef itk::RescaleIntensityImageFilter< OutImageType, OutImageType > RescaleFilterType;
typedef itk::WarpImageFilter<ImageType, OutImageType, DFImageType> WarpFilterType;

int main(int argc, char ** argv) {
  
  PARSE_ARGS;

  // Create a reader for the input
  ReaderType::Pointer reader_input = ReaderType::New(); // Input Volume
  DFReaderType::Pointer reader_DF = DFReaderType::New(); // Deformation field

  // Obtain values from the CLI
  const char * inputVolume = inVolume.c_str();
  const char * inputDF = deformationField.c_str();

  // Fill in the reader
  reader_input->SetFileName(inputVolume);
  reader_input->Update();
  reader_DF->SetFileName(inputDF);
  reader_DF->Update();

  // Create the warp filter and fill in the parameters
  WarpFilterType::Pointer warpFilter = WarpFilterType::New();
  warpFilter->SetInput(reader_input->GetOutput());
  warpFilter->SetDisplacementField(reader_DF->GetOutput());
  warpFilter->Update();

  //Apply the filter
  OutImageType::Pointer outImage = warpFilter->GetOutput();

  // Rescale the output volume intensities between 0 and 255
  // RescaleFilterType::Pointer rescaleFilter = RescaleFilterType::New();
  // rescaleFilter->SetInput(outImage);  
  // rescaleFilter->SetOutputMinimum(0);
  // rescaleFilter->SetOutputMaximum(255);
  

  // Create a writer for the output volume
  OutWriterType::Pointer OutWriter = OutWriterType::New();
  OutWriter->SetInput(outImage); 
  //OutWriter->SetInput(rescaleFilter->GetOutput());
  OutWriter->SetFileName(warpedVolume.c_str());  
  OutWriter->Update();

  return EXIT_SUCCESS;
}

