#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkConstrainedValueDifferenceImageFilter.h"

#include "SubtractorCLP.h"



typedef int PixelType;
const unsigned int Dimension = 3;

typedef itk::Image< PixelType, Dimension > ImageType; // We assume the input and output images have the same type

typedef itk::ImageFileReader< ImageType > ReaderType;
typedef itk::ImageFileWriter< ImageType > WriterType;

typedef itk::ConstrainedValueDifferenceImageFilter<ImageType, ImageType, ImageType> FilterType;


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
  

  // Create a writer for the output
  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(outputVolume.c_str());
  
  // Fill in the writer
  writer->SetInput(filter->GetOutput());
  writer->SetUseCompression(1);
  writer->Update();

  return EXIT_SUCCESS;

}
