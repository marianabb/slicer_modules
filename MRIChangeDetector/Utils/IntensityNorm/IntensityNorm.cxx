#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkN4BiasFieldCorrectionImageFilter.h"
//#include "itkImageRegionIteratorWithIndex.h"
//#include "itkCastImageFilter.h"
//#include "itkRescaleIntensityImageFilter.h"

#include "IntensityNormCLP.h"

typedef float PixelType;
typedef float OutPixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType;
typedef itk::Image< OutPixelType, Dimension > OutImageType;

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;
typedef itk::ImageFileWriter< OutImageType > OutWriterType;

//typedef itk::ImageRegionIteratorWithIndex<ImageType> IteratorType;

typedef itk::N4BiasFieldCorrectionImageFilter< ImageType, ImageType, OutImageType > N4BiasFilterType;
//typedef itk::CastImageFilter< ImageType, OutImageType > CastFilterType; // Filter to cast from ImageType to OutImageType
//typedef itk::RescaleIntensityImageFilter< OutImageType, OutImageType > RescaleFilterType;


int main(int argc, char ** argv) {
  
  PARSE_ARGS;

  // Create a reader for the input
  ReaderType::Pointer reader_input = ReaderType::New(); // Input Volume
  
  // Obtain values from the CLI
  const char * inputVolume = inVolume.c_str();

  // Fill in the reader
  reader_input->SetFileName(inputVolume);
  reader_input->Update();

  // Create the N4Bias filter and fill in the parameters
  N4BiasFilterType::Pointer normFilter = N4BiasFilterType::New();
  normFilter->SetInput(reader_input->GetOutput());
  normFilter->Update();

  OutImageType::Pointer outImage = normFilter->GetOutput();

  // Rescale the output volume intensities between 0 and 255
  // RescaleFilterType::Pointer rescaleFilter = RescaleFilterType::New();
  // rescaleFilter->SetInput(outImage);  
  // rescaleFilter->SetOutputMinimum(0);
  // rescaleFilter->SetOutputMaximum(255);
  

  // Create a writer for the output volume
  OutWriterType::Pointer OutWriter = OutWriterType::New();
  OutWriter->SetInput(outImage); 
  //OutWriter->SetInput(rescaleFilter->GetOutput());
  OutWriter->SetFileName(normalizedVolume.c_str());  
  OutWriter->Update();

  return EXIT_SUCCESS;
}

