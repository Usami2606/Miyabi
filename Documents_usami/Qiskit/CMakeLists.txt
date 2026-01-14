cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/common.cmake")

project(QuantumCircuitSimulatorServer C CXX)

# Dependency
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(Boost CONFIG REQUIRED COMPONENTS program_options)
find_package(fmt CONFIG REQUIRED)
find_package(jwt-cpp CONFIG REQUIRED)
find_package(quill CONFIG REQUIRED)

include(FetchContent)
FetchContent_Declare(
  readerwriterqueue
  GIT_REPOSITORY    https://github.com/cameron314/readerwriterqueue
  GIT_TAG           v1.0.6
)
FetchContent_MakeAvailable(readerwriterqueue)

# Find Protobuf installation
option(protobuf_MODULE_COMPATIBLE TRUE)
find_package(Protobuf CONFIG REQUIRED)
message(STATUS "Using protobuf ${Protobuf_VERSION}")
find_program(_PROTOBUF_PROTOC protoc)

# Find gRPC installation
find_package(gRPC CONFIG REQUIRED)
message(STATUS "Using gRPC ${gRPC_VERSION}")
find_program(_GRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)

# Directory for generated cpp files
set(pb_cpp_dir "${CMAKE_CURRENT_SOURCE_DIR}/pb_cpp")
# Create pb_cpp_dir if it does not exist
file(MAKE_DIRECTORY ${pb_cpp_dir})

# Proto file
get_filename_component(proto_abspath "${CMAKE_CURRENT_SOURCE_DIR}/proto/qc_simulator.proto" ABSOLUTE)
get_filename_component(proto_path "${proto_abspath}" PATH)

# Generate source files from proto
set(proto_srcs "${pb_cpp_dir}/qc_simulator.pb.cc")
set(proto_hdrs "${pb_cpp_dir}/qc_simulator.pb.h")
set(grpc_srcs "${pb_cpp_dir}/qc_simulator.grpc.pb.cc")
set(grpc_hdrs "${pb_cpp_dir}/qc_simulator.grpc.pb.h")

add_custom_command(
  OUTPUT "${proto_srcs}" "${proto_hdrs}" "${grpc_srcs}" "${grpc_hdrs}"
  COMMAND "${_PROTOBUF_PROTOC}"
  ARGS --grpc_out "${pb_cpp_dir}"
  --cpp_out "${pb_cpp_dir}"
  -I "${proto_path}"
  --plugin=protoc-gen-grpc="${_GRPC_CPP_PLUGIN_EXECUTABLE}"
  "${proto_abspath}"
  DEPENDS "${proto_abspath}")

# grpc_proto library
add_library(grpc_proto STATIC
  "${proto_srcs}" "${proto_hdrs}" "${grpc_srcs}" "${grpc_hdrs}"
)
target_include_directories(grpc_proto PRIVATE "${pb_cpp_dir}")
target_link_libraries(grpc_proto PRIVATE
  absl::check
  gRPC::grpc++
  gRPC::grpc++_reflection
  protobuf::libprotobuf
)

# Server program
add_executable(server "${CMAKE_CURRENT_SOURCE_DIR}/server/src/main.cpp")
target_include_directories(server SYSTEM PRIVATE "${Python3_INCLUDE_DIRS}")
target_include_directories(server PRIVATE "${pb_cpp_dir}")
target_link_libraries(server PRIVATE
  grpc_proto
  ${Python3_LIBRARIES}
  Boost::program_options
  fmt::fmt
  jwt-cpp::jwt-cpp
  quill::quill
  readerwriterqueue
  gRPC::grpc++
  gRPC::grpc++_reflection
  protobuf::libprotobuf
)
