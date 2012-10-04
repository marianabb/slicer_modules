#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkAbsoluteValueDifferenceImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"

#include "SubtractorCLP.h"



typedef float PixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType; // Input and output images have the same type

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;

typedef itk::AbsoluteValueDifferenceImageFilter<ImageType, ImageType, ImageType> FilterType;
typedef itk::RescaleIntensityImageFilter<ImageType, ImageType> RescaleFilterType;

int main( int argc, char ** argv ) {
  
  PARSE_ARGS;
  
  // Create readers for the inputs
  ReaderType::Pointer reader1 = ReaderType::New();
  ReaderType::Pointer reader2 = ReaderType::New();
  
  // Obtain values from the CLI
  const char * inputFilename1 = inputVolume1.c_str();
  const char * inputFilename2 = inputVolume2.c_str();
  
  reader1->SetFileName(inputFilename1);
  reader2->SetFileName(inputFilename2);
  
  // Fill in the readers
  reader1->Update();
  reader2->Update();

  // Create the filter and fill in the parameters
  FilterType::Pointer filter = FilterType::New();
  filter->SetInput1(reader1->GetOutput());
  filter->SetInput2(reader2->GetOutput());

  // Rescale the output volume intensities between 0 and 255
  RescaleFilterType::Pointer rescaleFilter = RescaleFilterType::New();
  rescaleFilter->SetInput(filter->GetOutput());  
  rescaleFilter->SetOutputMinimum(0);
  rescaleFilter->SetOutputMaximum(255);


  // Create a writer for the output
  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(outputVolume.c_str());
  
  // Fill in the writer
  //  writer->SetInput(filter->GetOutput());
  writer->SetInput(rescaleFilter->GetOutput());
  writer->SetUseCompression(1);
  writer->Update();

  return EXIT_SUCCESS;

}
