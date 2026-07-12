def _z_algorithm(seq):
    """Z[i] = length of the longest prefix of seq that starts at i."""
    n = len(seq)
    z = [0] * n
    left = right = 0

    for i in range(1, n):
        if i <= right:
            z[i] = min(right - i + 1, z[i - left])

        while i + z[i] < n and seq[z[i]] == seq[i + z[i]]:
            z[i] += 1

        if i + z[i] - 1 > right:
            left, right = i, i + z[i] - 1

    return z

def _is_concatenation_of_prefixes(prefix_text: str, block: str) -> bool:
    """
    True if prefix_text can be split into pieces where every piece is an
    exact prefix of block.

    Example:
        block = "Hello world"
        prefix_text = "HelloHello world"
        -> True, because "Hello" + "Hello world"
    """
    if not prefix_text:
        return True
    if not block:
        return False
    if prefix_text[0] != block[0]:
        return False

    # Build `block + separator + prefix_text` for Z/LCP calculation.
    # Use a string separator when possible; fall back to a unique object
    # so we never depend on a character not appearing in the text.
    sep = "\0"
    if sep not in block and sep not in prefix_text:
        combined = block + sep + prefix_text
    else:
        sentinel = object()
        combined = list(block)
        combined.append(sentinel)
        combined.extend(prefix_text)

    z = _z_algorithm(combined)

    block_len = len(block)
    prefix_len = len(prefix_text)
    offset = block_len + 1

    # Reachability over boundaries:
    # If position p is a valid chunk boundary, and prefix_text[p:] matches
    # block for k chars, then every p+1 ... p+k can be the next boundary.
    first_lcp = min(z[offset], block_len, prefix_len)
    if first_lcp == 0:
        return False

    max_reach = first_lcp
    pos = 1

    while pos <= max_reach and max_reach < prefix_len:
        lcp = min(z[offset + pos], block_len, prefix_len - pos)
        if lcp:
            max_reach = max(max_reach, pos + lcp)
        pos += 1

    return max_reach >= prefix_len

def _keep_last_repeated_block(text: str) -> str:
    """
    Repair text produced by a streaming bug like:

        prefix1 + prefix2 + prefix3 + final + final

    returning only:

        final

    Safety rule:
    - It only removes text when the ending is an EXACT repeated block.
    - It also verifies that everything before the last block can be split
      into exact prefixes of the kept block.
    - If that cannot be proven, it returns the original text unchanged.

    Note: No algorithm can distinguish every intentional repetition from a
    streaming bug without metadata. This function avoids fuzzy matching and
    only removes structurally proven repeated streaming snapshots.
    """
    n = len(text)
    if n < 2:
        return text

    # A repeated final block means text ends with B + B.
    # Instead of trying every B with slicing, reverse the text.
    # In reversed text, B+B at the end becomes rev(B)+rev(B) at the start.
    reversed_text = text[::-1]
    z_rev = _z_algorithm(reversed_text)

    # Try the largest repeated suffix first. This avoids shrinking a valid
    # final answer that itself contains smaller repetitions.
    for block_len in range(n // 2, 0, -1):
        if z_rev[block_len] < block_len:
            continue

        block = text[n - block_len:]

        # In the streaming bug model, the first emitted snapshot is also
        # a prefix of the final block.
        if not text or text[0] != block[0]:
            continue

        removed_part = text[: n - block_len]

        if _is_concatenation_of_prefixes(removed_part, block):
            return block

    return text

sample_1 = "Hey thereHey there! How's it going? What's on your mind today?Hey there! How's it going? What's on your mind today?"

sample_2 = """To addTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) projectTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

###To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependenciesTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implementTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project withTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets.To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets."""

sample_3 = """The capitalThe capital of France is **Paris**. 

It is located in the north-central part of the countryThe capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River.The capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River."""

sample_4 = """Here isHere is the quickest way to create and run a "Hello, World!" application in .NET usingHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new consoleHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
NavigateHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.csHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the applicationHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```"""

sample_5 = """Right?Right? I like to think so. 

What's on your mind? How can I help you outRight? I like to think so. 

What's on your mind? How can I help you out today?Right? I like to think so. 

What's on your mind? How can I help you out today?"""

print("sample 1: \n")
print(_keep_last_repeated_block(sample_1))

print("\n \n")
print("sample 2: \n")
print(_keep_last_repeated_block(sample_2))

print("\n \n")
print("sample 3: \n")
print(_keep_last_repeated_block(sample_3))

print("\n \n")
print("sample 4: \n")
print(_keep_last_repeated_block(sample_4))

print("\n \n")
print("sample 5: \n")
print(_keep_last_repeated_block(sample_5))